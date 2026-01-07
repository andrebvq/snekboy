"""
Visual test of PPU - shows screen buffer in terminal
"""

from src.cpu import CPU
import time

def print_screen_buffer(screen_buffer, chars=" .:-#"):
    """
    Print screen buffer to terminal using ASCII art

    Args:
        screen_buffer: 144x160 array of color values (0-3)
        chars: Characters to use for each color level
    """
    print("\033[2J\033[H")  # Clear screen and move to top
    print("="*80)
    print("SnekBoy PPU Visual Test (Terminal Mode)")
    print("="*80)

    # Sample every other row and every other column (to fit in terminal)
    for y in range(0, 144, 2):
        line = ""
        for x in range(0, 160, 2):
            color = screen_buffer[y][x]
            line += chars[color]
        print(line)

    print("="*80)

def test_checkerboard():
    """Test with checkerboard pattern"""
    cpu = CPU()

    print("Creating checkerboard pattern...")

    # Create checkerboard tile
    for i in range(8):
        if i % 2 == 0:
            cpu.memory.write_byte(0x8000 + i*2, 0xAA)      # 10101010
            cpu.memory.write_byte(0x8000 + i*2 + 1, 0x55)  # 01010101
        else:
            cpu.memory.write_byte(0x8000 + i*2, 0x55)      # 01010101
            cpu.memory.write_byte(0x8000 + i*2 + 1, 0xAA)  # 10101010

    # Create solid tiles for comparison
    # Tile 1: All color 0 (white)
    for i in range(8):
        cpu.memory.write_byte(0x8010 + i*2, 0x00)
        cpu.memory.write_byte(0x8010 + i*2 + 1, 0x00)

    # Tile 2: All color 3 (black)
    for i in range(8):
        cpu.memory.write_byte(0x8020 + i*2, 0xFF)
        cpu.memory.write_byte(0x8020 + i*2 + 1, 0xFF)

    # Fill tile map with pattern
    for y in range(32):
        for x in range(32):
            if (x + y) % 2 == 0:
                tile_num = 0  # Checkerboard
            elif y < 16:
                tile_num = 1  # White
            else:
                tile_num = 2  # Black
            cpu.memory.write_byte(0x9800 + y * 32 + x, tile_num)

    # Enable LCD
    cpu.memory.write_byte(0xFF40, 0x91)

    # Run for one frame
    print("Rendering frame...")
    for _ in range(70224 // 4):
        cpu.step()

    # Display result
    screen = cpu.ppu.get_screen_buffer()
    print_screen_buffer(screen)

    print(f"\nLY: {cpu.memory.read_byte(0xFF44)}")
    print(f"Mode: {cpu.memory.read_byte(0xFF41) & 0x03}")
    print(f"Total cycles: {cpu.total_cycles:,}")

def test_scrolling():
    """Test scrolling background"""
    cpu = CPU()

    print("Creating scrolling test pattern...")

    # Create vertical stripes tile
    for i in range(8):
        cpu.memory.write_byte(0x8000 + i*2, 0xF0)  # 11110000
        cpu.memory.write_byte(0x8000 + i*2 + 1, 0x0F)  # 00001111

    # Fill tile map
    for i in range(32 * 32):
        cpu.memory.write_byte(0x9800 + i, 0)

    # Enable LCD
    cpu.memory.write_byte(0xFF40, 0x91)

    # Animate scrolling
    for scroll_x in range(0, 64, 4):
        # Set scroll
        cpu.memory.write_byte(0xFF43, scroll_x)  # SCX

        # Run for one frame
        for _ in range(70224 // 4):
            cpu.step()

        # Display
        screen = cpu.ppu.get_screen_buffer()
        print_screen_buffer(screen)
        print(f"Scroll X: {scroll_x}")

        time.sleep(0.1)

if __name__ == '__main__':
    import sys

    if '--scroll' in sys.argv:
        test_scrolling()
    else:
        test_checkerboard()
        print("\nRun with --scroll to see scrolling animation")
