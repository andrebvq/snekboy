"""
Test basic PPU functionality
"""

from src.cpu import CPU

def test_ppu_initialization():
    """Test PPU initializes correctly"""
    cpu = CPU()

    # Check initial register values
    lcdc = cpu.memory.read_byte(0xFF40)
    stat = cpu.memory.read_byte(0xFF41)
    ly = cpu.memory.read_byte(0xFF44)

    print("PPU Initialization Test")
    print("="*60)
    print(f"LCDC (0xFF40): 0x{lcdc:02X}")
    print(f"STAT (0xFF41): 0x{stat:02X}")
    print(f"LY   (0xFF44): 0x{ly:02X}")

    assert lcdc == 0x91, f"Expected LCDC=0x91, got 0x{lcdc:02X}"
    assert ly == 0x00, f"Expected LY=0, got {ly}"

    print("[PASS] PPU initialized correctly")
    print()

def test_ppu_timing():
    """Test PPU mode timing"""
    cpu = CPU()

    print("PPU Timing Test")
    print("="*60)

    # Run for one scanline (456 T-cycles)
    for _ in range(114):  # 456 / 4 = 114 M-cycles
        cpu.step()

    ly = cpu.memory.read_byte(0xFF44)
    stat = cpu.memory.read_byte(0xFF41)
    mode = stat & 0x03

    print(f"After 456 T-cycles:")
    print(f"  LY: {ly}")
    print(f"  Mode: {mode}")

    assert ly == 1, f"Expected LY=1 after one scanline, got {ly}"
    print("[PASS] Scanline advanced correctly")
    print()

def test_vblank():
    """Test VBlank interrupt"""
    cpu = CPU()

    print("VBlank Interrupt Test")
    print("="*60)

    # Run until VBlank (144 scanlines * 456 cycles = 65664 cycles)
    target_cycles = 144 * 456
    while cpu.total_cycles < target_cycles:
        cpu.step()

    ly = cpu.memory.read_byte(0xFF44)
    if_reg = cpu.memory.read_byte(0xFF0F)
    vblank_flag = if_reg & 0x01

    print(f"After 144 scanlines:")
    print(f"  LY: {ly}")
    print(f"  IF register: 0x{if_reg:02X}")
    print(f"  VBlank flag (bit 0): {vblank_flag}")

    assert ly >= 144, f"Expected LY >= 144, got {ly}"
    assert vblank_flag != 0, "VBlank interrupt flag should be set"

    print("[PASS] VBlank interrupt triggered correctly")
    print()

def test_background_rendering():
    """Test background tile rendering"""
    cpu = CPU()

    print("Background Rendering Test")
    print("="*60)

    # Write a simple tile (all pixels = color 3)
    # Tile data: 2 bytes per line, 8 lines = 16 bytes
    for i in range(8):
        cpu.memory.write_byte(0x8000 + i*2, 0xFF)      # All 1s
        cpu.memory.write_byte(0x8000 + i*2 + 1, 0xFF)  # All 1s

    # Fill first row of tile map with tile 0
    for i in range(32):
        cpu.memory.write_byte(0x9800 + i, 0)

    # Enable LCD and background
    cpu.memory.write_byte(0xFF40, 0x91)

    # Run for one frame
    for _ in range(70224 // 4):
        cpu.step()

    # Check screen buffer
    screen = cpu.ppu.get_screen_buffer()

    # First row should have color 3 (darkest)
    first_row_colors = set(screen[0])

    print(f"Screen buffer first row colors: {sorted(first_row_colors)}")

    # With palette 0xFC (11 11 10 00), color 3 maps to color 3
    assert 3 in first_row_colors, "Expected color 3 in first row"

    print("[PASS] Background rendering works")
    print()

if __name__ == '__main__':
    test_ppu_initialization()
    test_ppu_timing()
    test_vblank()
    test_background_rendering()

    print("="*60)
    print("All PPU tests passed!")
