"""Run Tetris for longer to see if title screen appears"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

print(f"Loading ROM: {rom_path}")
cpu = CPU()
cpu.memory.load_rom_file(rom_path)

# Run for various cycle counts and check screen
test_points = [500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000]

for target_cycles in test_points:
    # Run to this point
    while cpu.total_cycles < target_cycles:
        try:
            cpu.step()
        except Exception as e:
            print(f"\nERROR at {cpu.total_cycles:,} cycles: {e}")
            break

    # Check screen
    screen = cpu.ppu.get_screen_buffer()
    from collections import Counter
    all_pixels = []
    for row in screen:
        all_pixels.extend(row)
    color_count = Counter(all_pixels)

    print(f"\n=== At {cpu.total_cycles:,} cycles ===")
    print(f"Color distribution:")
    for color in range(4):
        count = color_count.get(color, 0)
        percentage = (count / (160 * 144)) * 100
        print(f"  Color {color}: {percentage:5.2f}%")

    # Show a sample of the screen (middle rows)
    print(f"Screen sample (rows 70-73, cols 70-90):")
    for row in range(70, 74):
        pixels = "".join(str(screen[row][x]) for x in range(70, 90))
        print(f"  {pixels}")

    # Check LCDC
    lcdc = cpu.memory.read_byte(0xFF40)
    print(f"LCDC: 0x{lcdc:02X} (LCD {'ON' if lcdc & 0x80 else 'OFF'})")

print("\nDone")
