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
