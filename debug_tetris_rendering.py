"""
Debug Tetris rendering issues - screen tearing investigation
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def debug_ppu_state():
    """Debug PPU state during Tetris execution"""
    print("=" * 70)
    print("TETRIS PPU STATE DEBUG")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot to menu
    print("\nBooting to menu (500k cycles)...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    # Press START and get into gameplay
    print("Pressing START to enter game...")
    cpu.memory.joypad.press_button('start')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    for _ in range(100_000):
        cpu.step()

    print(f"\nIn-game at {cpu.total_cycles:,} cycles")
    print("\n" + "=" * 70)
    print("PPU REGISTER STATE")
    print("=" * 70)

    # Read all LCD registers
    lcdc = cpu.memory.read_byte(0xFF40)
    stat = cpu.memory.read_byte(0xFF41)
    scy = cpu.memory.read_byte(0xFF42)
    scx = cpu.memory.read_byte(0xFF43)
    ly = cpu.memory.read_byte(0xFF44)
    lyc = cpu.memory.read_byte(0xFF45)
    bgp = cpu.memory.read_byte(0xFF47)
    obp0 = cpu.memory.read_byte(0xFF48)
    obp1 = cpu.memory.read_byte(0xFF49)
    wy = cpu.memory.read_byte(0xFF4A)
    wx = cpu.memory.read_byte(0xFF4B)

    print(f"LCDC (0xFF40): 0x{lcdc:02X}")
    print(f"  Bit 7 (LCD Enable):        {(lcdc >> 7) & 1}")
    print(f"  Bit 6 (Window Tile Map):   {(lcdc >> 6) & 1} ({'0x9C00' if (lcdc >> 6) & 1 else '0x9800'})")
    print(f"  Bit 5 (Window Enable):     {(lcdc >> 5) & 1}")
    print(f"  Bit 4 (BG Tile Data):      {(lcdc >> 4) & 1} ({'0x8000' if (lcdc >> 4) & 1 else '0x8800'})")
    print(f"  Bit 3 (BG Tile Map):       {(lcdc >> 3) & 1} ({'0x9C00' if (lcdc >> 3) & 1 else '0x9800'})")
    print(f"  Bit 2 (Sprite Size):       {(lcdc >> 2) & 1} ({'8x16' if (lcdc >> 2) & 1 else '8x8'})")
    print(f"  Bit 1 (Sprite Enable):     {(lcdc >> 1) & 1}")
    print(f"  Bit 0 (BG Enable):         {lcdc & 1}")

    print(f"\nSTAT (0xFF41): 0x{stat:02X}")
    print(f"  Mode: {stat & 0x03} ({['HBlank', 'VBlank', 'OAM Search', 'Pixel Transfer'][stat & 0x03]})")
    print(f"  LYC=LY Coincidence: {(stat >> 2) & 1}")

    print(f"\nScroll: SCY={scy}, SCX={scx}")
    print(f"LY (Scanline): {ly}")
    print(f"LYC (Compare): {lyc}")
    print(f"BGP (Palette): 0x{bgp:02X}")
    print(f"OBP0: 0x{obp0:02X}, OBP1: 0x{obp1:02X}")
    print(f"Window: WY={wy}, WX={wx}")

    print("\n" + "=" * 70)
    print("PPU INTERNAL STATE")
    print("=" * 70)
    print(f"Current Mode: {cpu.ppu.current_mode}")
    print(f"Cycle Counter: {cpu.ppu.cycle_counter}")
    print(f"Expected cycles for mode:")
    print(f"  Mode 2 (OAM): {cpu.ppu.MODE_2_CYCLES}")
    print(f"  Mode 3 (Transfer): {cpu.ppu.MODE_3_CYCLES}")
    print(f"  Mode 0 (HBlank): {cpu.ppu.MODE_0_CYCLES}")
    print(f"  Scanline total: {cpu.ppu.SCANLINE_CYCLES}")

    print("\n" + "=" * 70)
    print("SCREEN BUFFER ANALYSIS")
    print("=" * 70)

    screen = cpu.ppu.get_screen_buffer()

    # Count colors per scanline
    print("\nColors per scanline (first 20 scanlines):")
    for y in range(min(20, len(screen))):
        colors = set(screen[y])
        if len(colors) > 1:
            print(f"  Line {y:3d}: {len(colors)} colors - {sorted(colors)}")
        else:
            print(f"  Line {y:3d}: {len(colors)} color  - {sorted(colors)}")

    # Overall stats
    all_colors = set()
    for row in screen:
        all_colors.update(row)

    print(f"\nTotal colors used: {sorted(all_colors)}")
    print(f"Total unique colors: {len(all_colors)}")

    # Check if there's a pattern (tearing might show as repeated lines)
    print("\nChecking for repeated scanlines (tearing symptom):")
    repeated = 0
    for y in range(len(screen) - 1):
        if screen[y] == screen[y + 1]:
            repeated += 1
    print(f"  Repeated scanlines: {repeated}/143")

    # Sample VRAM content
    print("\n" + "=" * 70)
    print("VRAM SAMPLE (First 32 bytes of tile data)")
    print("=" * 70)
    vram_sample = []
    for i in range(32):
        vram_sample.append(cpu.memory.read_byte(0x8000 + i))

    print("0x8000: " + " ".join(f"{b:02X}" for b in vram_sample[:16]))
    print("0x8010: " + " ".join(f"{b:02X}" for b in vram_sample[16:32]))

    # Check if VRAM has any data
    vram_nonzero = 0
    for i in range(0x8000, 0x9800):
        if cpu.memory.read_byte(i) != 0:
            vram_nonzero += 1
    print(f"\nNon-zero VRAM bytes: {vram_nonzero}/6144 ({vram_nonzero*100/6144:.1f}%)")

    # Sample tile map
    print("\n" + "=" * 70)
    print("TILE MAP SAMPLE (First 32 bytes)")
    print("=" * 70)
    tile_map_base = 0x9C00 if (lcdc & 0x08) else 0x9800
    tilemap_sample = []
    for i in range(32):
        tilemap_sample.append(cpu.memory.read_byte(tile_map_base + i))

    print(f"0x{tile_map_base:04X}: " + " ".join(f"{b:02X}" for b in tilemap_sample[:16]))
    print(f"0x{tile_map_base+16:04X}: " + " ".join(f"{b:02X}" for b in tilemap_sample[16:32]))


def check_scanline_timing():
    """Check if scanlines are timing correctly"""
    print("\n" + "=" * 70)
    print("SCANLINE TIMING CHECK")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    while cpu.total_cycles < 500_000:
        cpu.step()

    print("\nMonitoring LY register for 2 frames...")

    ly_changes = []
    prev_ly = cpu.memory.read_byte(0xFF44)
    start_cycles = cpu.total_cycles

    # Monitor for 2 frames
    frame_cycles = 70224 * 2

    while cpu.total_cycles < start_cycles + frame_cycles:
        cpu.step()
        curr_ly = cpu.memory.read_byte(0xFF44)

        if curr_ly != prev_ly:
            cycles_elapsed = cpu.total_cycles - start_cycles
            ly_changes.append((cycles_elapsed, prev_ly, curr_ly))
            prev_ly = curr_ly

    print(f"\nLY changes detected: {len(ly_changes)}")
    print("\nFirst 10 LY transitions:")
    for i, (cycles, old_ly, new_ly) in enumerate(ly_changes[:10]):
        print(f"  {i+1}. Cycle {cycles:6d}: LY {old_ly:3d} -> {new_ly:3d}")

    # Calculate average cycles per scanline
    if len(ly_changes) > 2:
        cycle_diffs = []
        for i in range(1, min(len(ly_changes), 154)):
            cycle_diff = ly_changes[i][0] - ly_changes[i-1][0]
            cycle_diffs.append(cycle_diff)

        avg_cycles = sum(cycle_diffs) / len(cycle_diffs)
        print(f"\nAverage cycles per scanline: {avg_cycles:.1f}")
        print(f"Expected: 456 T-cycles")
        print(f"Difference: {avg_cycles - 456:.1f} cycles")


if __name__ == '__main__':
    debug_ppu_state()
    check_scanline_timing()
