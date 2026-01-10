"""Visualize what Tetris is actually showing"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

cpu = CPU()
cpu.memory.load_rom_file(rom_path)

# Run for 2M cycles
while cpu.total_cycles < 2_000_000:
    cpu.step()

# Get screen buffer and visualize it
screen = cpu.ppu.get_screen_buffer()

# Use ASCII art to show the screen
print("Tetris Screen (first 80 rows, full width):")
print("(0 = space, 3 = #)")
print("-" * 160)

for y in range(80):
    line = ""
    for x in range(160):
        pixel = screen[y][x]
        if pixel == 0:
            line += " "
        elif pixel == 1:
            line += "."
        elif pixel == 2:
            line += "+"
        else:  # 3
            line += "#"
    print(line)

print("-" * 160)
