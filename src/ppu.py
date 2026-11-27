"""
Game Boy PPU (Picture Processing Unit) Implementation

The PPU renders graphics to a 160x144 pixel screen at 60 FPS.

LCD Registers:
- LCDC (0xFF40): LCD Control - enable/disable LCD, background, sprites, etc.
- STAT (0xFF41): LCD Status - mode flags, interrupts
- SCY  (0xFF42): Scroll Y - background vertical scroll
- SCX  (0xFF43): Scroll X - background horizontal scroll
- LY   (0xFF44): Line Y - current scanline being drawn (0-153)
- LYC  (0xFF45): LY Compare - triggers interrupt when LY == LYC
- BGP  (0xFF47): Background Palette - color mapping for background
- OBP0 (0xFF48): Object Palette 0 - color mapping for sprites
- OBP1 (0xFF49): Object Palette 1 - color mapping for sprites
- WY   (0xFF4A): Window Y position
- WX   (0xFF4B): Window X position

PPU Modes (in STAT register):
- Mode 0: HBlank (207 cycles) - CPU can access VRAM/OAM
- Mode 1: VBlank (4560 cycles, 10 scanlines) - CPU can access VRAM/OAM
- Mode 2: OAM Search (80 cycles) - CPU cannot access OAM
- Mode 3: Pixel Transfer (172 cycles) - CPU cannot access VRAM/OAM

One scanline: Mode 2 (80) -> Mode 3 (172) -> Mode 0 (207) = 459 cycles
One frame: 144 scanlines + 10 vblank lines = 154 scanlines = 70224 cycles
"""

# A tile row is two bytes: byte 1 holds bit 0 and byte 2 bit 1 of each pixel's
# colour number, leftmost pixel in bit 7. TILE_ROW[(byte1 << 8) | byte2] gives
# the 8 colour numbers (0-3) of that row, so rendering needs one lookup per tile.
TILE_ROW = tuple(
    tuple((((b2 >> bit) & 1) << 1) | ((b1 >> bit) & 1) for bit in range(7, -1, -1))
    for b1 in range(256) for b2 in range(256)
)


class PPU:
    """Game Boy Picture Processing Unit"""

    # Screen dimensions
    SCREEN_WIDTH = 160
    SCREEN_HEIGHT = 144

    # Timing constants (in T-cycles, not M-cycles!)
    MODE_2_CYCLES = 80   # OAM Search
    MODE_3_CYCLES = 172  # Pixel Transfer
    MODE_0_CYCLES = 204  # HBlank (456 - 80 - 172)
    SCANLINE_CYCLES = 456  # Total cycles per scanline
    VBLANK_LINES = 10
    TOTAL_LINES = 154  # 144 visible + 10 vblank

    # PPU Modes
    MODE_HBLANK = 0
    MODE_VBLANK = 1
    MODE_OAM_SEARCH = 2
    MODE_PIXEL_TRANSFER = 3

    def __init__(self, memory, interrupt_callback=None):
        """
        Initialize PPU

        Args:
            memory: Memory object to read/write registers and VRAM
            interrupt_callback: Function to call for interrupts (VBlank, STAT)
        """
        self.memory = memory
        self.interrupt_callback = interrupt_callback

        # Screen buffer: 160x144 pixels, each pixel is 0-3 (2-bit color)
        self.screen_buffer = [[0 for _ in range(self.SCREEN_WIDTH)]
                              for _ in range(self.SCREEN_HEIGHT)]

        # Timing
        self.cycle_counter = 0  # Cycles in current scanline
        self.current_mode = self.MODE_OAM_SEARCH

        # Initialize registers to power-on state
        self._init_registers()

    def _init_registers(self):
        """Initialize LCD registers to power-on values"""
        self.memory._data[0xFF40] = 0x91  # LCDC: LCD on, BG on
        self.memory._data[0xFF41] = 0x85  # STAT: mode 1
        self.memory._data[0xFF42] = 0x00  # SCY
        self.memory._data[0xFF43] = 0x00  # SCX
        self.memory._data[0xFF44] = 0x00  # LY (scanline)
        self.memory._data[0xFF45] = 0x00  # LYC
        self.memory._data[0xFF47] = 0xFC  # BGP (11 11 10 00)
        self.memory._data[0xFF48] = 0xFF  # OBP0
        self.memory._data[0xFF49] = 0xFF  # OBP1
        self.memory._data[0xFF4A] = 0x00  # WY
        self.memory._data[0xFF4B] = 0x00  # WX

    def step(self, cycles: int):
        """
        Update PPU for the given number of CPU cycles

        Args:
            cycles: Number of T-cycles that have elapsed
        """
        # Check if LCD is enabled
        lcdc = self.memory._data[0xFF40]
        ly = self.memory._data[0xFF44]

        if not (lcdc & 0x80):  # Bit 7 = LCD enable
            # LCD is off - advance cycles and LY to simulate timing, but no rendering
            # This is critical: real hardware continues LY counter even when LCD is off
            # Games rely on this to poll LY and detect VBlank timing
            self.cycle_counter += cycles

            while self.cycle_counter >= self.SCANLINE_CYCLES:
                self.cycle_counter -= self.SCANLINE_CYCLES
                ly = (ly + 1) % 154  # Wrap 0-153
                self.memory._data[0xFF44] = ly
                self._check_lyc_coincidence()  # Still check LYC coincidence

                # Trigger VBlank interrupt when entering VBlank region, even with LCD off
                # This is critical for games that turn off LCD and rely on VBlank for timing
                if ly == 144:
                    # Enter VBlank mode
                    if self.current_mode != self.MODE_VBLANK:
                        self._set_mode(self.MODE_VBLANK)
                    # Trigger VBlank interrupt
                    if self.interrupt_callback:
                        self.interrupt_callback(0)  # VBlank interrupt (bit 0)

            return

        self.cycle_counter += cycles

        # Check which mode we're in based on current scanline and cycle count
        if ly >= 144:
            # VBlank period (lines 144-153)
            if self.current_mode != self.MODE_VBLANK:
                self._enter_vblank()

            # Check if we should move to next scanline
            if self.cycle_counter >= self.SCANLINE_CYCLES:
                self.cycle_counter -= self.SCANLINE_CYCLES
                ly += 1

                if ly > 153:
                    # End of frame, restart
                    ly = 0
                    self._enter_oam_search()

                self.memory._data[0xFF44] = ly
                self._check_lyc_coincidence()

        else:
            # Visible scanlines (0-143)
            if self.cycle_counter <= self.MODE_2_CYCLES:
                # Mode 2: OAM Search
                if self.current_mode != self.MODE_OAM_SEARCH:
                    self._enter_oam_search()

            elif self.cycle_counter <= (self.MODE_2_CYCLES + self.MODE_3_CYCLES):
                # Mode 3: Pixel Transfer
                if self.current_mode != self.MODE_PIXEL_TRANSFER:
                    # Entering mode 3 - render scanline once
                    self._set_mode(self.MODE_PIXEL_TRANSFER)
                    self._render_scanline(ly)

            else:
                # Mode 0: HBlank
                if self.current_mode != self.MODE_HBLANK:
                    self._enter_hblank()

                # Check if we should move to next scanline
                if self.cycle_counter >= self.SCANLINE_CYCLES:
                    self.cycle_counter -= self.SCANLINE_CYCLES
                    ly += 1
                    self.memory._data[0xFF44] = ly
                    self._check_lyc_coincidence()

                    if ly == 144:
                        # Entering VBlank
                        self._enter_vblank()
                    else:
                        # Next scanline starts with OAM search
                        self._enter_oam_search()

    def _set_mode(self, mode: int):
        """Set PPU mode and update STAT register"""
        self.current_mode = mode
        stat = self.memory._data[0xFF41]
        # Clear lower 2 bits and set new mode
        stat = (stat & 0xFC) | mode
        self.memory._data[0xFF41] = stat

    def _enter_vblank(self):
        """Enter VBlank mode and request VBlank interrupt"""
        self._set_mode(self.MODE_VBLANK)

        # Request VBlank interrupt (bit 0 of IF)
        if self.interrupt_callback:
            self.interrupt_callback(0)

        # Also check for STAT interrupt (bit 4 of STAT = VBlank interrupt enable)
        stat = self.memory._data[0xFF41]
        if stat & 0x10:  # VBlank interrupt enabled
            if self.interrupt_callback:
                self.interrupt_callback(1)  # STAT interrupt

    def _enter_hblank(self):
        """Enter HBlank mode and potentially request STAT interrupt"""
        self._set_mode(self.MODE_HBLANK)

        # Check for HBlank STAT interrupt (bit 3 of STAT)
        stat = self.memory._data[0xFF41]
        if stat & 0x08:  # HBlank interrupt enabled
            if self.interrupt_callback:
                self.interrupt_callback(1)  # STAT interrupt

    def _enter_oam_search(self):
        """Enter OAM Search mode and potentially request STAT interrupt"""
        self._set_mode(self.MODE_OAM_SEARCH)

        # Check for OAM Search STAT interrupt (bit 5 of STAT)
        stat = self.memory._data[0xFF41]
        if stat & 0x20:  # OAM interrupt enabled
            if self.interrupt_callback:
                self.interrupt_callback(1)  # STAT interrupt

    def _check_lyc_coincidence(self):
        """Check if LY == LYC and set coincidence flag"""
        ly = self.memory._data[0xFF44]
        lyc = self.memory._data[0xFF45]
        stat = self.memory._data[0xFF41]

        if ly == lyc:
            # Set coincidence flag (bit 2)
            stat |= 0x04

            # Check if LYC interrupt is enabled (bit 6)
            if stat & 0x40:
                if self.interrupt_callback:
                    self.interrupt_callback(1)  # STAT interrupt
        else:
            # Clear coincidence flag
            stat &= ~0x04

        self.memory._data[0xFF41] = stat

    def _render_scanline(self, ly: int):
        """
        Render a single scanline (background + window + sprites)

        Args:
            ly: Current scanline number (0-143)
        """
        lcdc = self.memory._data[0xFF40]

        # Render background first
        self._render_background_scanline(ly, lcdc)

        # Render window on top of background (if enabled)
        if lcdc & 0x20:  # Bit 5 = window enable
            self._render_window_scanline(ly, lcdc)

        # Render sprites on top (if enabled)
        if lcdc & 0x02:  # Bit 1 = sprite enable
            self._render_sprites_scanline(ly, lcdc)

    def _tile_line_pixels(self, d, map_row: int, first_col: int, tiles: int,
                          signed: bool, tile_line: int) -> list:
        """Colour numbers for `tiles` consecutive tiles of one tile-map row.

        The PPU reads VRAM directly: CPU access rules don't apply to it.
        """
        pixels = []
        line_offset = tile_line * 2
        for i in range(tiles):
            tile_num = d[map_row + ((first_col + i) & 31)]
            if signed:
                # Signed tile numbers (-128..127) relative to 0x9000
                addr = 0x9000 + ((tile_num ^ 0x80) - 0x80) * 16 + line_offset
            else:
                addr = 0x8000 + tile_num * 16 + line_offset
            pixels.extend(TILE_ROW[(d[addr] << 8) | d[addr + 1]])
        return pixels

    def _render_background_scanline(self, ly: int, lcdc: int):
        """
        Render background for a single scanline

        Args:
            ly: Current scanline number (0-143)
            lcdc: LCD control register value
        """
        row = self.screen_buffer[ly]

        # Check if background is enabled (bit 0)
        if not (lcdc & 0x01):
            # Background disabled - render blank line
            row[:] = [0] * self.SCREEN_WIDTH
            return

        d = self.memory._data
        scy = d[0xFF42]
        scx = d[0xFF43]
        bgp = d[0xFF47]
        palette = [(bgp >> (i * 2)) & 0x03 for i in range(4)]

        # Background tile map: bit 3 of LCDC (0 = 0x9800, 1 = 0x9C00)
        tile_map_base = 0x9C00 if (lcdc & 0x08) else 0x9800
        # Tile data: bit 4 of LCDC (0 = signed from 0x9000, 1 = unsigned from 0x8000)
        signed = not (lcdc & 0x10)

        # Row of the 256x256 background this scanline shows
        y_pos = (ly + scy) & 0xFF
        map_row = tile_map_base + (y_pos >> 3) * 32

        # 21 tiles cover 160 pixels at any fine X scroll; the map wraps every 32 tiles
        pixels = self._tile_line_pixels(d, map_row, scx >> 3, 21, signed, y_pos & 7)
        fine_x = scx & 7
        row[:] = [palette[c] for c in pixels[fine_x:fine_x + self.SCREEN_WIDTH]]

    def _render_window_scanline(self, ly: int, lcdc: int):
        """
        Render window for a single scanline

        The window is an alternative background area that is displayed on top of the background.
        It has no transparency - it always covers the background.

        Args:
            ly: Current scanline number (0-143)
            lcdc: LCD control register value
        """
        d = self.memory._data
        wy = d[0xFF4A]  # Window Y position
        wx = d[0xFF4B]  # Window X position minus 7

        # Check if window is visible on this scanline
        if ly < wy:
            return  # Window hasn't started yet

        # Window tile map: bit 6 of LCDC (0 = 0x9800, 1 = 0x9C00)
        tile_map_base = 0x9C00 if (lcdc & 0x40) else 0x9800
        # Window uses same tile data as background (bit 4 of LCDC)
        signed = not (lcdc & 0x10)

        # Window line: which line of the window we're rendering
        window_y = ly - wy

        # WX=7 means window starts at screen X=0
        window_x_start = max(0, wx - 7)
        width = self.SCREEN_WIDTH - window_x_start
        if width <= 0:
            return

        bgp = d[0xFF47]  # window uses the background palette
        palette = [(bgp >> (i * 2)) & 0x03 for i in range(4)]
        map_row = tile_map_base + (window_y >> 3) * 32
        pixels = self._tile_line_pixels(d, map_row, 0, (width + 7) >> 3, signed, window_y & 7)

        # Window overwrites background
        self.screen_buffer[ly][window_x_start:] = [palette[c] for c in pixels[:width]]

    def _render_sprites_scanline(self, ly: int, lcdc: int):
        """
        Render sprites for a single scanline

        Args:
            ly: Current scanline number (0-143)
            lcdc: LCD control register value
        """
        # Sprite size: bit 2 of LCDC (0 = 8x8, 1 = 8x16)
        sprite_height = 16 if (lcdc & 0x04) else 8

        # OAM is at 0xFE00-0xFE9F (160 bytes = 40 sprites, 4 bytes each)
        # Sprite attributes:
        # Byte 0: Y position (minus 16)
        # Byte 1: X position (minus 8)
        # Byte 2: Tile number
        # Byte 3: Flags (priority, Y flip, X flip, palette)

        sprites_on_line = []
        d = self.memory._data  # the PPU reads OAM and VRAM directly

        # Scan all 40 sprites
        for sprite_index in range(40):
            oam_addr = 0xFE00 + (sprite_index * 4)

            y_pos = d[oam_addr]
            x_pos = d[oam_addr + 1]
            tile_num = d[oam_addr + 2]
            flags = d[oam_addr + 3]

            # Adjust positions (hardware stores Y-16, X-8)
            y_pos = y_pos - 16
            x_pos = x_pos - 8

            # Check if sprite is on this scanline
            if ly >= y_pos and ly < y_pos + sprite_height:
                sprites_on_line.append({
                    'x': x_pos,
                    'y': y_pos,
                    'tile': tile_num,
                    'flags': flags,
                    'index': sprite_index
                })

        # Limit to 10 sprites per scanline (hardware limitation)
        sprites_on_line = sprites_on_line[:10]

        # Sort sprites by priority (lower X = higher priority, then lower OAM index = higher priority)
        # We render in reverse order, so sort descending (highest priority last = rendered on top)
        sprites_on_line.sort(key=lambda s: (-s['x'], -s['index']))

        # Render sprites (reversed order means lowest X / lowest index renders last = on top)
        for sprite in sprites_on_line:
            x_pos = sprite['x']
            y_pos = sprite['y']
            tile_num = sprite['tile']
            flags = sprite['flags']

            # Parse flags
            priority = (flags >> 7) & 1  # 0 = sprite above BG, 1 = sprite behind BG colors 1-3
            y_flip = (flags >> 6) & 1
            x_flip = (flags >> 5) & 1
            palette_num = (flags >> 4) & 1  # 0 = OBP0, 1 = OBP1

            # Get palette
            palette_addr = 0xFF48 if palette_num == 0 else 0xFF49
            palette = d[palette_addr]

            # Calculate which line of the sprite we're rendering
            sprite_line = ly - y_pos

            # Handle Y flip
            if y_flip:
                sprite_line = (sprite_height - 1) - sprite_line

            # For 8x16 sprites, tile_num uses bit 0 to select top/bottom tile
            if sprite_height == 16:
                if sprite_line >= 8:
                    tile_num = (tile_num & 0xFE) | 0x01  # Bottom tile
                    sprite_line -= 8
                else:
                    tile_num = tile_num & 0xFE  # Top tile

            # Sprites always use 0x8000 addressing mode
            tile_addr = 0x8000 + (tile_num * 16) + (sprite_line * 2)

            # Read tile data
            byte1 = d[tile_addr]
            byte2 = d[tile_addr + 1]

            # Render each pixel of the sprite
            for pixel_x in range(8):
                screen_x = x_pos + pixel_x

                # Skip if off-screen
                if screen_x < 0 or screen_x >= self.SCREEN_WIDTH:
                    continue

                # Get bit position (handle X flip)
                if x_flip:
                    bit_pos = pixel_x
                else:
                    bit_pos = 7 - pixel_x

                # Get color index
                color_bit_low = (byte1 >> bit_pos) & 1
                color_bit_high = (byte2 >> bit_pos) & 1
                color_index = (color_bit_high << 1) | color_bit_low

                # Color 0 is transparent for sprites
                if color_index == 0:
                    continue

                # Get background color at this position
                bg_color_index = self.screen_buffer[ly][screen_x]

                # Check priority
                if priority == 1:
                    # Sprite is behind background colors 1-3
                    if bg_color_index != 0:
                        continue  # Don't draw sprite pixel

                # Apply sprite palette
                color = (palette >> (color_index * 2)) & 0x03

                # Draw sprite pixel
                self.screen_buffer[ly][screen_x] = color

    def get_screen_buffer(self):
        """
        Get the current screen buffer

        Returns:
            List[List[int]]: 144x160 array of color values (0-3)
        """
        return self.screen_buffer

    def reset(self):
        """Reset PPU to power-on state"""
        self.cycle_counter = 0
        self.current_mode = self.MODE_OAM_SEARCH
        self._init_registers()

        # Clear screen buffer
        for y in range(self.SCREEN_HEIGHT):
            for x in range(self.SCREEN_WIDTH):
                self.screen_buffer[y][x] = 0
