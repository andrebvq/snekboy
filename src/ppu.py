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
        lcdc = self.memory.read_byte(0xFF40)
        if not (lcdc & 0x80):  # Bit 7 = LCD enable
            # LCD is off - reset to mode 0, LY = 0
            self.memory._data[0xFF44] = 0  # LY
            self._set_mode(self.MODE_HBLANK)
            self.cycle_counter = 0
            return

        self.cycle_counter += cycles
        ly = self.memory.read_byte(0xFF44)

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
                    self._set_mode(self.MODE_OAM_SEARCH)

                self.memory._data[0xFF44] = ly
                self._check_lyc_coincidence()

        else:
            # Visible scanlines (0-143)
            if self.cycle_counter <= self.MODE_2_CYCLES:
                # Mode 2: OAM Search
                if self.current_mode != self.MODE_OAM_SEARCH:
                    self._set_mode(self.MODE_OAM_SEARCH)

            elif self.cycle_counter <= (self.MODE_2_CYCLES + self.MODE_3_CYCLES):
                # Mode 3: Pixel Transfer
                if self.current_mode != self.MODE_PIXEL_TRANSFER:
                    self._set_mode(self.MODE_PIXEL_TRANSFER)
                    # Render this scanline
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
                        self._set_mode(self.MODE_OAM_SEARCH)

    def _set_mode(self, mode: int):
        """Set PPU mode and update STAT register"""
        self.current_mode = mode
        stat = self.memory.read_byte(0xFF41)
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
        stat = self.memory.read_byte(0xFF41)
        if stat & 0x10:  # VBlank interrupt enabled
            if self.interrupt_callback:
                self.interrupt_callback(1)  # STAT interrupt

    def _enter_hblank(self):
        """Enter HBlank mode and potentially request STAT interrupt"""
        self._set_mode(self.MODE_HBLANK)

        # Check for HBlank STAT interrupt (bit 3 of STAT)
        stat = self.memory.read_byte(0xFF41)
        if stat & 0x08:  # HBlank interrupt enabled
            if self.interrupt_callback:
                self.interrupt_callback(1)  # STAT interrupt

    def _check_lyc_coincidence(self):
        """Check if LY == LYC and set coincidence flag"""
        ly = self.memory.read_byte(0xFF44)
        lyc = self.memory.read_byte(0xFF45)
        stat = self.memory.read_byte(0xFF41)

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
        Render a single scanline (background only for now)

        Args:
            ly: Current scanline number (0-143)
        """
        lcdc = self.memory.read_byte(0xFF40)

        # Check if background is enabled (bit 0)
        if not (lcdc & 0x01):
            # Background disabled - render blank line
            for x in range(self.SCREEN_WIDTH):
                self.screen_buffer[ly][x] = 0
            return

        # Get scroll positions
        scy = self.memory.read_byte(0xFF42)
        scx = self.memory.read_byte(0xFF43)

        # Background tile map: bit 3 of LCDC
        # 0 = 0x9800-0x9BFF, 1 = 0x9C00-0x9FFF
        tile_map_base = 0x9C00 if (lcdc & 0x08) else 0x9800

        # Background tile data: bit 4 of LCDC
        # 0 = 0x8800-0x97FF (signed addressing), 1 = 0x8000-0x8FFF (unsigned)
        tile_data_base = 0x8000 if (lcdc & 0x10) else 0x8800
        use_signed = not (lcdc & 0x10)

        # Calculate which row of the 256x256 background we're on
        y_pos = (ly + scy) & 0xFF

        # Which tile row (0-31, since 256 pixels / 8 pixels per tile = 32 tiles)
        tile_row = y_pos // 8

        # Which line within that tile (0-7)
        tile_line = y_pos % 8

        # Render each pixel in this scanline
        for x in range(self.SCREEN_WIDTH):
            # Calculate X position in 256x256 background
            x_pos = (x + scx) & 0xFF

            # Which tile column (0-31)
            tile_col = x_pos // 8

            # Which pixel within that tile (0-7)
            tile_pixel = x_pos % 8

            # Get tile number from tile map
            tile_map_addr = tile_map_base + (tile_row * 32) + tile_col

            # PPU needs unrestricted access to VRAM during rendering
            self.memory._bypass_ppu_restrictions = True
            tile_num = self.memory.read_byte(tile_map_addr)

            # Calculate tile data address
            if use_signed:
                # Signed addressing: treat tile_num as signed byte
                if tile_num > 127:
                    tile_num = tile_num - 256
                tile_addr = tile_data_base + (tile_num * 16) + (tile_line * 2)
            else:
                # Unsigned addressing
                tile_addr = tile_data_base + (tile_num * 16) + (tile_line * 2)

            # Read tile data (2 bytes per line, 1 bit from each byte per pixel)
            byte1 = self.memory.read_byte(tile_addr)
            byte2 = self.memory.read_byte(tile_addr + 1)
            self.memory._bypass_ppu_restrictions = False

            # Get color index (0-3) for this pixel
            # Bit 7 is leftmost pixel, bit 0 is rightmost
            bit_pos = 7 - tile_pixel
            color_bit_low = (byte1 >> bit_pos) & 1
            color_bit_high = (byte2 >> bit_pos) & 1
            color_index = (color_bit_high << 1) | color_bit_low

            # Apply background palette
            bgp = self.memory.read_byte(0xFF47)
            color = (bgp >> (color_index * 2)) & 0x03

            # Store in screen buffer
            self.screen_buffer[ly][x] = color

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
