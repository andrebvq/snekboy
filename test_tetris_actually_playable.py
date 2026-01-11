"""
Test if Tetris is actually playable now
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

    chars = [' ', '.', '+', '#']

    print("+" + "-" * 40 + "+")
    for y in range(0, 144, 4):
        line = "|"
        for x in range(0, 160, 4):
            # Sample 4x4 block
            avg = 0
            for dy in range(4):
                for dx in range(4):
                    if y+dy < 144 and x+dx < 160:
                        avg += screen[y+dy][x+dx]
            avg = avg // 16
            line += chars[min(avg, 3)]
        line += "|"
        print(line)
    print("+" + "-" * 40 + "+")


def test_gameplay():
    """Test actual Tetris gameplay"""
    print("="*70)
    print("TETRIS PLAYABILITY TEST")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    print("\n1. Booting to title screen (500k cycles)...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    show_screen_ascii(screen, "After Boot - Title Screen")

    # Press START to enter menu
    print("\n2. Pressing START to enter game mode selection...")
    cpu.memory.joypad.press_button('start')

    for _ in range(50_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for _ in range(100_000):
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    show_screen_ascii(screen, "After START - Mode Selection")

    # Check if screen changed
    non_bg = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\nScreen has {non_bg:,} non-background pixels")

    # Press START again to select A-TYPE and start game
    print("\n3. Pressing START again to start A-TYPE game...")
    cpu.memory.joypad.press_button('start')

    for _ in range(50_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for _ in range(300_000):
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    show_screen_ascii(screen, "After Second START - Should Be In Game")

    # Check for gameplay elements
    non_bg = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\nScreen has {non_bg:,} non-background pixels")

    # Look for game field (should have borders, score, etc.)
    print("\nLooking for gameplay elements...")

    # Sample different regions
    # Top region (score area)
    top_pixels = sum(1 for y in range(20) for x in range(160) if screen[y][x] != 0)

    # Middle region (play field)
    mid_pixels = sum(1 for y in range(40, 140) for x in range(40, 120) if screen[y][x] != 0)

    print(f"Top region (score): {top_pixels} non-bg pixels")
    print(f"Middle region (field): {mid_pixels} non-bg pixels")

    if top_pixels > 100 and mid_pixels > 100:
        print("\nLooks like we're in the game! Elements detected.")
    elif mid_pixels > 100:
        print("\nSome game elements visible")
    else:
        print("\nScreen might still be loading...")

    # Try moving a piece
    print("\n4. Testing piece movement - pressing LEFT...")
    for _ in range(100_000):
        cpu.step()

    cpu.memory.joypad.press_button('left')

    for _ in range(20_000):
        cpu.step()

    cpu.memory.joypad.release_button('left')

    for _ in range(50_000):
        cpu.step()

    screen_after_move = cpu.ppu.get_screen_buffer()

    # Check if screen changed
    changes = sum(1 for y in range(144) for x in range(160)
                  if screen[y][x] != screen_after_move[y][x])

    print(f"\nPixels changed after pressing LEFT: {changes}")

    if changes > 10:
        print("Screen changed significantly - piece might have moved!")
    elif changes > 0:
        print("Small screen change detected")
    else:
        print("No screen change - might be stuck or pieces not moving")

    show_screen_ascii(screen_after_move, "After Pressing LEFT")

    # Final verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)

    if top_pixels > 100 and mid_pixels > 100:
        print("Tetris appears to be PLAYABLE!")
        print("You should be able to:")
        print("  - See the game field")
        print("  - See score/level display")
        print("  - Control pieces with arrow keys")
    else:
        print("Game might not have fully loaded to gameplay yet")
        print("Try running for more cycles or pressing more buttons")


if __name__ == '__main__':
    test_gameplay()
