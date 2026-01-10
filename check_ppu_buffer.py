"""Check the actual PPU screen buffer contents"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

print(f"Loading ROM: {rom_path}")
cpu = CPU()
cpu.memory.load_rom_file(rom_path)

# Run for a bit
cycles_run = 0
max_cycles = 2_000_000

while cycles_run < max_cycles:
    cycles = cpu.step()
    cycles_run += cycles

print(f"Ran {cycles_run:,} cycles\n")

# Get screen buffer
screen = cpu.ppu.get_screen_buffer()

# Check the actual data in the buffer
print("Analyzing screen buffer...")
print(f"Screen buffer type: {type(screen)}")
print(f"Screen buffer length: {len(screen)}")
if len(screen) > 0:
    print(f"First row type: {type(screen[0])}")
    print(f"First row length: {len(screen[0])}")

# Get color statistics
from collections import Counter
all_pixels = []
for row in screen:
    all_pixels.extend(row)

color_count = Counter(all_pixels)
print(f"\nColor distribution across entire screen:")
for color, count in sorted(color_count.items()):
    percentage = (count / (160 * 144)) * 100
    print(f"  Color {color}: {count:5d} pixels ({percentage:5.2f}%)")

# Check for vertical stripe pattern
print("\nChecking columns 0-19 of row 0:")
row0 = screen[0]
print("  " + "".join(str(row0[x]) for x in range(20)))

print("\nChecking columns 0-19 of row 1:")
row1 = screen[1]
print("  " + "".join(str(row1[x]) for x in range(20)))

# Check if there's an alternating pattern
print("\nColumn-by-column analysis (first 20 columns, first 10 rows):")
for col in range(20):
    column_pixels = [screen[row][col] for row in range(10)]
    unique = len(set(column_pixels))
    print(f"  Col {col:2d}: {' '.join(str(p) for p in column_pixels)} (unique: {unique})")

# Check middle of screen too
print("\nMiddle of screen (rows 70-74, cols 0-19):")
for row in range(70, 75):
    pixels = "".join(str(screen[row][x]) for x in range(20))
    print(f"  Row {row}: {pixels}")
