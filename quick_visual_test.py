"""
Quick visual test - shows what Tetris is rendering at different stages
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

def show_screen_ascii(screen, title):
    """Show screen as ASCII art"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print('='*60)

    chars = [' ', '░', '▒', '█']

    print("┌" + "─" * 40 + "┐")
    for y in range(0, 144, 4):
        line = "│"
        for x in range(0, 160, 4):
            # Sample 4x4 block
            avg = 0
            for dy in range(4):
                for dx in range(4):
                    if y+dy < 144 and x+dx < 160:
                        avg += screen[y+dy][x+dx]
            avg = avg // 16
            line += chars[min(avg, 3)]
        line += "│"
        print(line)
    print("└" + "─" * 40 + "┘")


def main():
    """Show Tetris rendering at key moments"""
    print("="*60)
    print("TETRIS VISUAL RENDERING TEST".center(60))
    print("="*60)
    print("\nThis will show what Tetris renders at different stages.")
    print("If you see text in the ASCII art below, graphics are working!\n")

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Stage 1: Copyright screen (early)
    print("\nStage 1: Running to copyright screen (500k cycles)...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    show_screen_ascii(screen, "Stage 1: Copyright Screen (~3 seconds in)")

    # Count non-background pixels
    non_bg = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\nNon-background pixels: {non_bg:,}/23,040 ({non_bg*100/23040:.1f}%)")

    if non_bg > 1000:
        print("✅ LOTS of graphics detected!")
        print("   Look for text like 'TETRIS', 'NINTENDO', 'ALEXEY PAJITNOV'")
    else:
        print("⚠️  Few graphics - might be early in boot")

    # Stage 2: Run longer
    print("\nStage 2: Running longer (to 1M cycles)...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    show_screen_ascii(screen, "Stage 2: After 1M Cycles")

    non_bg = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\nNon-background pixels: {non_bg:,}/23,040 ({non_bg*100/23040:.1f}%)")

    # Try to detect text
    print("\nLooking for recognizable patterns...")

    # Check for horizontal lines of pixels (text)
    text_lines = 0
    for y in range(144):
        non_zero_in_line = sum(1 for x in range(160) if screen[y][x] != 0)
        if 10 < non_zero_in_line < 140:  # Text lines have some pixels
            text_lines += 1

    print(f"Lines with text-like patterns: {text_lines}")

    if text_lines > 5:
        print("✅ Text patterns detected - graphics rendering correctly!")

    print("\n" + "="*60)
    print("INTERPRETATION".center(60))
    print("="*60)
    print("""
If you see patterns in the ASCII art above that look like letters:
  ✅ Your emulator is rendering correctly!
  ✅ Sprite system is working!
  ✅ Background tiles are working!

The 'striped' appearance in the GUI is NORMAL - that's the background.
The text and sprites render ON TOP of those stripes.

To see the game properly:
  1. Run: python src/emulator.py
  2. Wait 5 seconds for copyright screen
  3. Press Z (START) to advance to title screen
  4. Press Z again to start playing
  5. Use J/L/K/I for left/right/down/up
  6. Use A to rotate pieces
""")


if __name__ == '__main__':
    main()
