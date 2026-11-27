"""PPU rendering checks against Pan Docs "Tile Data" / "LCDC"."""

from src.cpu import CPU


def test_signed_tile_numbers_use_base_0x9000():
    cpu = CPU()
    cpu.memory.load_rom(bytes(0x8000))
    cpu.simulate_boot()
    d = cpu.memory._data
    d[0x9800] = 0x00                  # map entry: tile 0
    d[0x9000:0x9010] = bytes([0xFF, 0x00] * 8)   # tile 0 in signed mode: colour 1
    d[0x8800:0x8810] = bytes([0xFF, 0xFF] * 8)   # wrong base would give colour 3
    d[0xFF47] = 0xE4                  # identity palette
    d[0xFF42] = d[0xFF43] = 0         # no scroll
    cpu.ppu._render_background_scanline(0, 0x81)   # LCD on, BG on, LCDC.4 = 0
    assert cpu.ppu.get_screen_buffer()[0][0] == 1


# --- helpers ------------------------------------------------------------------

def _booted():
    cpu = CPU()
    cpu.memory.load_rom(bytes(0x8000))
    cpu.simulate_boot()
    return cpu


def _tile(d, n, colour):
    """Tile n at 0x8000 filled with one colour number."""
    lo = 0xFF if colour & 1 else 0x00
    hi = 0xFF if colour & 2 else 0x00
    d[0x8000 + n * 16:0x8000 + n * 16 + 16] = bytes([lo, hi] * 8)


def _irq_counter(ppu):
    hits = []
    ppu.interrupt_callback = lambda bit: hits.append((bit, ppu.ly, ppu.cycle_counter))
    return hits


def _to_line_start(ppu, ly):
    while not (ppu.ly == ly and ppu.cycle_counter < 4):
        ppu.step(4)


# --- window -------------------------------------------------------------------

def test_window_keeps_its_own_line_counter():
    """Window hidden on lines 4-11 resumes at its row 4 on line 12, not row 12."""
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    _tile(d, 0, 1)
    _tile(d, 1, 2)
    d[0x9800:0x9820] = bytes([0] * 32)            # window rows 0-7: tile 0
    d[0x9820:0x9840] = bytes([1] * 32)            # window rows 8-15: tile 1
    d[0xFF47], d[0xFF4A], d[0xFF4B] = 0xE4, 0, 7
    ppu._wy_hit = True
    for ly in range(13):
        lcdc = 0x91 if 4 <= ly < 12 else 0xB1      # window off on lines 4-11
        d[0xFF40] = lcdc
        ppu._render_scanline(ly)
    assert ppu.screen_buffer[12][0] == 1          # window row 4 -> tile 0


def test_window_hidden_when_background_off():
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    _tile(d, 0, 3)
    d[0x9800] = 0
    d[0xFF47], d[0xFF4A], d[0xFF4B] = 0xE4, 0, 7
    ppu._wy_hit = True
    d[0xFF40] = 0xB0                              # window on, BG (bit 0) off
    ppu._render_scanline(0)
    assert ppu.screen_buffer[0][0] == 0


def test_window_x_below_7_shifts_left():
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    _tile(d, 0, 0)
    _tile(d, 1, 3)
    d[0x9800], d[0x9801] = 0, 1
    d[0xFF47], d[0xFF4A], d[0xFF4B] = 0xE4, 0, 3
    ppu._wy_hit = True
    d[0xFF40] = 0xB1
    ppu._render_scanline(0)
    assert ppu.screen_buffer[0][:8] == [0, 0, 0, 0, 3, 3, 3, 3]


# --- sprites ------------------------------------------------------------------

def _sprite(d, i, x, y, tile, flags):
    d[0xFE00 + i * 4:0xFE04 + i * 4] = bytes([y + 16, x + 8, tile, flags])


def test_behind_bg_sprite_checks_colour_number_not_shade():
    """BG colour 0 mapped to black by BGP: a behind-BG sprite still shows."""
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    _tile(d, 0, 0)                                # BG tile: colour 0
    _tile(d, 1, 1)                                # sprite tile: colour 1
    d[0x9800:0x9820] = bytes(32)
    d[0xFF47] = 0x03                              # BG colour 0 -> shade 3
    d[0xFF48] = 0xE4
    _sprite(d, 0, 0, 0, 1, 0x80)                  # behind BG
    d[0xFF40] = 0x93
    ppu._render_scanline(0)
    assert ppu.screen_buffer[0][0] == 1


def test_overlapping_sprites_lower_x_wins_even_when_hidden():
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    _tile(d, 0, 2)                                # BG colour 2 everywhere
    _tile(d, 1, 1)                                # sprite tile
    d[0x9800:0x9820] = bytes(32)
    d[0xFF47], d[0xFF48] = 0xE4, 0xFC             # sprite colour 1 -> shade 3
    _sprite(d, 0, 10, 0, 1, 0x80)                 # x=10, behind BG: hidden
    _sprite(d, 1, 12, 0, 1, 0x00)                 # x=12, in front
    d[0xFF40] = 0x93
    ppu._render_scanline(0)
    row = ppu.screen_buffer[0]
    assert row[12:18] == [2] * 6                  # first sprite owns these pixels
    assert row[18:20] == [3, 3]                   # only second sprite here


# --- LCD on/off ---------------------------------------------------------------

def test_lcd_off_stops_ppu_and_restarts_at_line_0():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    _to_line_start(ppu, 10)
    mem.write_byte(0xFF40, 0x11)                  # LCD off
    hits = _irq_counter(ppu)
    for _ in range(70224 // 4):
        ppu.step(4)
    assert mem.read_byte(0xFF44) == 0
    assert mem.read_byte(0xFF41) & 0x03 == 0
    assert hits == []
    mem.write_byte(0xFF40, 0x91)                  # LCD on
    assert ppu.ly == 0 and ppu.cycle_counter == 0
    assert mem.read_byte(0xFF41) & 0x03 == 0      # first line: no OAM-search mode


# --- STAT -----------------------------------------------------------------------

def test_stat_interrupt_only_on_rising_edge():
    """HBlank + LYC sources: the LYC match on line 3 follows line 2's HBlank, no new edge."""
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    _to_line_start(ppu, 0)
    mem.write_byte(0xFF45, 3)
    mem.write_byte(0xFF41, 0x48)
    hits = _irq_counter(ppu)
    _to_line_start(ppu, 5)
    assert [ly for bit, ly, _ in hits if bit == 1] == [0, 1, 2, 4]


def test_stat_write_keeps_read_only_bits():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    _to_line_start(ppu, 2)
    ppu.step(100)                                 # mode 3
    mem.write_byte(0xFF41, 0x07)
    assert mem.read_byte(0xFF41) == 0x83          # mode 3, LYC flag clear (LY=2, LYC=0)


def test_lyc_write_matching_ly_sets_flag_and_interrupt():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    _to_line_start(ppu, 5)
    mem.write_byte(0xFF41, 0x40)
    hits = _irq_counter(ppu)
    mem.write_byte(0xFF45, 5)
    assert mem.read_byte(0xFF41) & 0x04
    assert hits and hits[0][0] == 1


def test_line_153_reads_ly_0_and_matches_lyc_0():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    _to_line_start(ppu, 153)
    ppu.step(8)
    assert ppu.ly == 153
    assert mem.read_byte(0xFF44) == 0
    assert mem.read_byte(0xFF41) & 0x04           # LYC=0 matches already


def test_post_boot_stat_matches_ppu_mode():
    cpu = _booted()
    assert cpu.memory.read_byte(0xFF41) & 0x03 == cpu.ppu.current_mode == 1
    assert cpu.memory.read_byte(0xFF44) == 0


# --- line timing (mooneye lcdon_timing / lcdon_write_timing / intr_2_*) ----------

def _dot(ppu, ly, dot):
    _to_line_start(ppu, ly)
    ppu.step(dot - ppu.cycle_counter)


def test_ly_advances_4_dots_before_the_line_ends():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    mem.write_byte(0xFF45, 1)
    _dot(ppu, 0, 448)
    assert mem.read_byte(0xFF44) == 0
    ppu.step(4)                                   # dot 452
    assert mem.read_byte(0xFF44) == 1
    assert not mem.read_byte(0xFF41) & 0x04       # LYC flag waits for the new line
    assert mem.read_byte(0xFF41) & 0x03 == 0      # still HBlank
    ppu.step(4)                                   # dot 0 of line 1
    assert mem.read_byte(0xFF41) & 0x07 == 0x06   # mode 2, LYC flag set


def test_access_locks_around_mode_3():
    cpu = _booted()
    ppu = cpu.ppu
    _dot(ppu, 1, 72)
    assert ppu.oam_locked and ppu.oam_write_locked and not ppu.vram_locked
    ppu.step(4)                                   # dot 76
    assert ppu.vram_locked and not ppu.vram_write_locked
    assert ppu.oam_locked and not ppu.oam_write_locked
    ppu.step(4)                                   # dot 80: mode 3
    assert ppu.vram_write_locked and ppu.oam_write_locked
    _dot(ppu, 1, 448)
    assert not ppu.oam_locked
    ppu.step(4)                                   # dot 452
    assert ppu.oam_locked and not ppu.oam_write_locked


def test_mode_3_longer_with_scroll_and_sprites():
    cpu = _booted()
    d, ppu = cpu.memory._data, cpu.ppu
    d[0xFF40] = 0x93                              # sprites on
    d[0xFF43] = 5                                 # SCX fine scroll 5
    for i in range(10):
        _sprite(d, i, 0, 2, 0, 0)                 # 10 sprites at screen X 0 (OAM X 8), line 2
    _dot(ppu, 2, 84)
    # SCX adds 5. Sprites: OAM X 8 + 5 lands at pixel 5 of a tile -> 6 + 0 for the
    # first, 6 for each of the other 9 (same tile); minus the 3-dot calibration.
    assert ppu._mode3_end == 252 + 5 + (6 + 9 * 6) - 3


def test_first_line_after_lcd_on_has_no_early_locks():
    cpu = _booted()
    mem, ppu = cpu.memory, cpu.ppu
    mem.write_byte(0xFF40, 0x11)
    mem.write_byte(0xFF40, 0x91)
    ppu.step(76)
    assert not ppu.vram_locked and not ppu.oam_locked
    ppu.step(4)
    assert ppu.vram_locked and mem.read_byte(0xFF41) & 0x03 == 3
