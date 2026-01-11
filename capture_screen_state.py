"""
Capture exact screen state to understand what's being rendered
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def analyze_screen():
    """Analyze what's actually on screen"""
    print("=" * 70)
    print("SCREEN STATE ANALYSIS")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Run for a while
    print("\nRunning 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()

    # Find non-zero pixels
    print("\nFinding non-zero pixels...")
    non_zero_pixels = []
    for y in range(144):
        for x in range(160):
            if screen[y][x] != 0:
                non_zero_pixels.append((x, y, screen[y][x]))

    print(f"Non-zero pixels found: {len(non_zero_pixels)}")

    if len(non_zero_pixels) > 0:
        print("\nFirst 50 non-zero pixels:")
        for i, (x, y, color) in enumerate(non_zero_pixels[:50]):
            print(f"  ({x:3d},{y:3d}) = color {color}")

        # Find bounding box
        min_x = min(p[0] for p in non_zero_pixels)
        max_x = max(p[0] for p in non_zero_pixels)
        min_y = min(p[1] for p in non_zero_pixels)
        max_y = max(p[1] for p in non_zero_pixels)

        print(f"\nBounding box: ({min_x},{min_y}) to ({max_x},{max_y})")
        print(f"Size: {max_x - min_x + 1}x{max_y - min_y + 1} pixels")

        # Show a zoomed view of the non-zero region
        print("\nZoomed view of non-zero region:")
        chars = [' ', '░', '▒', '█']

        for y in range(max(0, min_y - 2), min(144, max_y + 3)):
            line = f"{y:3d} |"
            for x in range(max(0, min_x - 2), min(160, max_x + 3)):
                color = screen[y][x]
                line += chars[color]
            print(line)

if __name__ == '__main__':
    analyze_screen()
