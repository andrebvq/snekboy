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
- Mode 2: OAM Search (80 dots) - CPU cannot access OAM
- Mode 3: Pixel Transfer (172 dots here; really 172-289) - CPU cannot access VRAM/OAM
- Mode 0: HBlank (rest of the 456-dot line) - CPU can access VRAM/OAM
- Mode 1: VBlank (lines 144-153) - CPU can access VRAM/OAM

One frame: 154 lines x 456 dots = 70224 T-cycles
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
        # Colour numbers (before the palette) of the BG/window on the line being
        # drawn; sprite-behind-background priority tests these, not shades.
        self._bg_index = [0] * self.SCREEN_WIDTH

        self._reset_state()
        self._init_registers()

    def _reset_state(self):
        self.ly = 0                 # internal line; the LY register differs on line 153
        self.cycle_counter = 0      # dot within the current line (0-455)
        self._phase = self.MODE_OAM_SEARCH        # where the PPU is in the line
        self.current_mode = self.MODE_OAM_SEARCH  # what STAT reports (and what locks memory)
        self._lcd_on = True
        self._stat_line = False     # the four STAT sources ORed together
        self._window_line = 0       # the window's own line counter
        self._wy_hit = False        # LY has reached WY this frame
        # CPU access locks. Reads lock a few dots before STAT shows the mode;
        # writes follow slightly different edges (mooneye lcdon_*timing tests).
        self.oam_locked = False     # OAM reads blocked: last 4 dots of the line before, to end of mode 3
        self.oam_write_locked = False   # OAM writes blocked: dots 0-75 and mode 3
        self.vram_locked = False    # VRAM reads blocked: dot 76 to end of mode 3
        self.vram_write_locked = False  # VRAM writes blocked: mode 3
        self._first_line = False    # first line after LCD on: no OAM search, no early locks
        self._line_ending = False   # in the last 4 dots of the line, LY already advanced
        self._mode3_end = 252       # dot where pixel transfer ends on this line

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

    def post_boot_state(self):
        """State when the boot ROM hands over: the end of line 153, in VBlank.

        LY already reads 0 there (see the line-153 note in step), which is why
        the boot ROM leaves LY=0 with STAT in mode 1.
        """
        self._reset_state()
        self.ly = 153
        self.cycle_counter = 400
        self._phase = self.current_mode = self.MODE_VBLANK
        d = self.memory._data
        d[0xFF44] = 0
        d[0xFF41] = (d[0xFF41] & 0xFC) | self.MODE_VBLANK
        self._compare_lyc()
        self._stat_line = self._stat_sources()

    # --- LCD on/off ------------------------------------------------------------

    def lcdc_written(self):
        """Called after every LCDC write; handles the LCD being switched on or off."""
        on = bool(self.memory._data[0xFF40] & 0x80)
        if on != self._lcd_on:
            if on:
                self._lcd_switch_on()
            else:
                self._lcd_switch_off()

    def _lcd_switch_off(self):
        # The PPU stops: LY reads 0, STAT reports mode 0, no interrupts, and the
        # screen goes blank. The LY=LYC flag keeps its last value.
        d = self.memory._data
        self._lcd_on = False
        self.ly = 0
        self.cycle_counter = 0
        self._phase = self.current_mode = self.MODE_HBLANK
        self._unlock()
        self._line_ending = False
        d[0xFF44] = 0
        d[0xFF41] &= 0xFC
        # The frozen LY=LYC flag keeps its STAT source high (or low) while off
        self._stat_line = (d[0xFF41] & 0x44) == 0x44
        for row in self.screen_buffer:
            row[:] = [0] * self.SCREEN_WIDTH

    def _lcd_switch_on(self):
        # Restart at line 0, dot 0. The first line has no OAM-search period:
        # STAT reports mode 0 until pixel transfer starts.
        self._lcd_on = True
        self.ly = 0
        self.cycle_counter = 0
        self._phase = self.MODE_OAM_SEARCH
        self.current_mode = self.MODE_HBLANK
        self._first_line = True
        self._line_ending = False
        self._unlock()
        self._window_line = 0
        self._wy_hit = self.memory._data[0xFF4A] == 0
        self._compare_lyc()
        self._update_stat()

    # --- STAT ------------------------------------------------------------------

    def _compare_lyc(self):
        d = self.memory._data
        if d[0xFF44] == d[0xFF45]:
            d[0xFF41] |= 0x04
        else:
            d[0xFF41] &= ~0x04

    def _stat_sources(self, oam_at_144=False):
        stat = self.memory._data[0xFF41]
        mode = stat & 0x03
        return bool(
            (stat & 0x44) == 0x44
            or (mode == 0 and stat & 0x08)
            or (mode == 1 and (stat & 0x10 or (oam_at_144 and stat & 0x20)))
            or (mode == 2 and stat & 0x20)
        )

    def _update_stat(self, oam_at_144=False):
        """Request the STAT interrupt only when the combined STAT line goes 0 -> 1."""
        line = self._stat_sources(oam_at_144)
        if line and not self._stat_line and self.interrupt_callback:
            self.interrupt_callback(1)
        self._stat_line = line

    def stat_written(self):
        if self._lcd_on:
            self._update_stat()

    def lyc_written(self):
        # While the LCD is off the comparison is frozen.
        if self._lcd_on:
            self._compare_lyc()
            self._update_stat()

    def _set_mode(self, mode: int):
        """Set PPU mode and update STAT register"""
        self._phase = self.current_mode = mode
        d = self.memory._data
        d[0xFF41] = (d[0xFF41] & 0xFC) | mode
        self._update_stat()

    # --- timing ----------------------------------------------------------------

    def step(self, cycles: int):
        """
        Update PPU for the given number of CPU cycles

        Args:
            cycles: Number of T-cycles that have elapsed
        """
        d = self.memory._data
        if not (d[0xFF40] & 0x80):
            if self._lcd_on:
                self._lcd_switch_off()
            return
        if not self._lcd_on:
            self._lcd_switch_on()

        self.cycle_counter += cycles
        while True:
            dot = self.cycle_counter
            phase = self._phase
            if phase == self.MODE_OAM_SEARCH:
                if dot < 76:
                    return
                if not self._first_line and not self.vram_locked:
                    self.vram_locked = True     # VRAM reads lock 4 dots before mode 3 shows
                    self.oam_write_locked = False   # while OAM writes briefly pass
                if dot < 80:
                    return
                self._first_line = False
                self.oam_locked = self.oam_write_locked = True
                self.vram_locked = self.vram_write_locked = True
                self._set_mode(self.MODE_PIXEL_TRANSFER)
                self._mode3_end = 252 + self._render_scanline(self.ly)
            elif phase == self.MODE_PIXEL_TRANSFER:
                if dot < self._mode3_end:
                    return
                self._unlock()
                self._set_mode(self.MODE_HBLANK)
            else:  # HBlank or VBlank
                if phase == self.MODE_VBLANK and self.ly == 153 and dot >= 4 and d[0xFF44] != 0:
                    # Line 153: LY reads 153 only for the first few dots, then 0
                    d[0xFF44] = 0
                    self._compare_lyc()
                    self._update_stat()
                if dot < 452:
                    return
                if not self._line_ending:
                    self._end_line()
                if dot < 456:
                    return
                self._next_line()

    def dots_to_next_event(self):
        """T-cycles until step() next changes the mode, LY or the STAT/VBlank
        interrupt lines (lock-only points included, to stay conservative).
        Between events, advancing in one call or in many gives the same
        result. None while the LCD is off (no events); 0 if an LCD on/off
        switch is still to be processed."""
        lcd = self.memory._data[0xFF40] & 0x80
        if not lcd:
            return None if not self._lcd_on else 0
        if not self._lcd_on:
            return 0
        dot = self.cycle_counter
        phase = self._phase
        if phase == self.MODE_OAM_SEARCH:
            target = 76 if dot < 76 else 80
        elif phase == self.MODE_PIXEL_TRANSFER:
            target = self._mode3_end
        elif (phase == self.MODE_VBLANK and self.ly == 153 and dot < 4
              and self.memory._data[0xFF44] != 0):
            target = 4
        elif dot < 452:
            target = 452
        else:
            target = 456
        return target - dot

    def _unlock(self):
        self.oam_locked = self.oam_write_locked = False
        self.vram_locked = self.vram_write_locked = False

    def _end_line(self):
        """Last 4 dots of a line: LY already shows the next line, the LY=LYC
        flag reads 0 until the comparison runs at the new line, and OAM locks
        if a visible line follows. From line 153 to line 0 LY stays 0, so the
        flag (and any LYC=0 interrupt line) stays as it is."""
        d = self.memory._data
        self._line_ending = True
        ly = self.ly
        if ly < 153:
            d[0xFF44] = ly + 1
            d[0xFF41] &= ~0x04
            self._update_stat()
        if ly < 143 or ly == 153:
            self.oam_locked = True

    def _next_line(self):
        d = self.memory._data
        self.cycle_counter -= 456
        self._line_ending = False
        ly = self.ly + 1
        if ly == 154:
            ly = 0
        self.ly = ly
        d[0xFF44] = ly
        self._compare_lyc()

        if ly < 144:
            if ly == d[0xFF4A]:
                self._wy_hit = True
            self.oam_write_locked = True
            self._set_mode(self.MODE_OAM_SEARCH)
        elif ly == 144:
            self._phase = self.current_mode = self.MODE_VBLANK
            d[0xFF41] = (d[0xFF41] & 0xFC) | self.MODE_VBLANK
            if self.interrupt_callback:
                self.interrupt_callback(0)
            # On DMG the OAM STAT source also fires as line 144 starts.
            self._update_stat(oam_at_144=True)
            self._update_stat()
            self._window_line = 0
            self._wy_hit = False
        else:
            self._update_stat()

    # --- rendering -------------------------------------------------------------

    def _render_scanline(self, ly: int):
        """
        Render a single scanline (background + window + sprites)

        Args:
            ly: Current scanline number (0-143)
        """
        d = self.memory._data
        lcdc = d[0xFF40]
        scx = d[0xFF43]
        # Pixel transfer gets longer for fine X scroll, the window and sprites
        penalty = scx & 7

        # Render background first
        self._render_background_scanline(ly, lcdc)

        # Window on top of background. On DMG, LCDC bit 0 off blanks both.
        if lcdc & 0x21 == 0x21 and self._render_window_scanline(ly, lcdc):
            penalty += 6

        # Render sprites on top (if enabled)
        if lcdc & 0x02:  # Bit 1 = sprite enable
            penalty += self._render_sprites_scanline(ly, lcdc, scx)
        return penalty

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
            self._bg_index = [0] * self.SCREEN_WIDTH
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
        index = pixels[fine_x:fine_x + self.SCREEN_WIDTH]
        self._bg_index = index
        row[:] = [palette[c] for c in index]

    def _render_window_scanline(self, ly: int, lcdc: int):
        """
        Render window for a single scanline

        The window is an alternative background area that is displayed on top of the background.
        It has no transparency - it always covers the background. It starts once LY has
        reached WY in this frame, and keeps its own line counter, which only advances on
        lines where the window was actually drawn.

        Args:
            ly: Current scanline number (0-143)
            lcdc: LCD control register value
        """
        d = self.memory._data
        wx = d[0xFF4B]  # Window X position plus 7
        if not self._wy_hit or wx > 166:
            return False

        # Window tile map: bit 6 of LCDC (0 = 0x9800, 1 = 0x9C00)
        tile_map_base = 0x9C00 if (lcdc & 0x40) else 0x9800
        # Window uses same tile data as background (bit 4 of LCDC)
        signed = not (lcdc & 0x10)

        window_y = self._window_line
        self._window_line += 1

        # WX=7 puts the window at screen X=0; below 7 it is shifted left
        x_start = max(0, wx - 7)
        skip = x_start - (wx - 7)
        width = self.SCREEN_WIDTH - x_start

        bgp = d[0xFF47]  # window uses the background palette
        palette = [(bgp >> (i * 2)) & 0x03 for i in range(4)]
        map_row = tile_map_base + (window_y >> 3) * 32
        pixels = self._tile_line_pixels(d, map_row, 0, (skip + width + 7) >> 3, signed, window_y & 7)
        pixels = pixels[skip:skip + width]

        # Window overwrites background
        self.screen_buffer[ly][x_start:] = [palette[c] for c in pixels]
        self._bg_index[x_start:] = pixels
        return True

    def _render_sprites_scanline(self, ly: int, lcdc: int, scx: int = 0) -> int:
        """
        Render sprites for a single scanline

        Up to 10 sprites per line, the first ones found in OAM. Where sprites
        overlap, the one with the smaller X wins (then the lower OAM index), and
        it wins even when its pixel is then hidden behind the background.

        Args:
            ly: Current scanline number (0-143)
            lcdc: LCD control register value
        """
        height = 16 if (lcdc & 0x04) else 8
        d = self.memory._data  # the PPU reads OAM and VRAM directly

        # OAM: 40 sprites x 4 bytes (Y+16, X+8, tile, flags)
        found = []
        for addr in range(0xFE00, 0xFEA0, 4):
            top = d[addr] - 16
            if top <= ly < top + height:
                found.append((d[addr + 1], addr))
                if len(found) == 10:
                    break
        if not found:
            return 0
        found.sort()        # smaller X first, then lower OAM address

        # Each fetched sprite stalls pixel transfer 6 dots, plus up to 5 more
        # the first time its background tile is hit, depending on where in that
        # tile it starts (Pan Docs, "Mode 3 length"). Sprites at X >= 168
        # aren't fetched.
        penalty = 0
        tiles_seen = set()
        for x_raw, _ in found:
            if x_raw < 168:
                pos = x_raw + (scx & 7)
                tile = pos >> 3
                penalty += 6
                if tile not in tiles_seen:
                    tiles_seen.add(tile)
                    penalty += max(0, 5 - (pos & 7))

        row = self.screen_buffer[ly]
        bg = self._bg_index
        taken = [False] * self.SCREEN_WIDTH
        for x_raw, addr in found:
            x0 = x_raw - 8
            if x0 <= -8 or x0 >= self.SCREEN_WIDTH:
                continue
            tile = d[addr + 2]
            flags = d[addr + 3]
            line = ly - (d[addr] - 16)
            if flags & 0x40:                      # Y flip
                line = height - 1 - line
            if height == 16:                      # bit 0 of the tile picks the half
                tile = (tile & 0xFE) | (line >> 3)
                line &= 7
            tile_addr = 0x8000 + tile * 16 + line * 2
            pixels = TILE_ROW[(d[tile_addr] << 8) | d[tile_addr + 1]]
            if flags & 0x20:                      # X flip
                pixels = pixels[::-1]
            palette = d[0xFF49] if flags & 0x10 else d[0xFF48]
            behind = flags & 0x80                 # behind BG colours 1-3

            for k in range(8):
                x = x0 + k
                if 0 <= x < self.SCREEN_WIDTH and not taken[x]:
                    c = pixels[k]
                    if c:                         # colour 0 is transparent
                        taken[x] = True
                        if not (behind and bg[x]):
                            row[x] = (palette >> (c * 2)) & 0x03
        # Calibrated against mooneye intr_2_mode0_timing_sprites (DMG data): seen
        # at this emulator's 4-dot resolution, the stall ends 3 dots earlier.
        return max(0, penalty - 3)

    def get_screen_buffer(self):
        """
        Get the current screen buffer

        Returns:
            List[List[int]]: 144x160 array of color values (0-3)
        """
        return self.screen_buffer

    def reset(self):
        """Reset PPU to power-on state"""
        self._reset_state()
        self._init_registers()

        # Clear screen buffer
        for row in self.screen_buffer:
            row[:] = [0] * self.SCREEN_WIDTH
