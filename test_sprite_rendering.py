"""
Test if sprite rendering is working
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

def test_sprite_rendering():
    """Test if sprites are being rendered"""
    print("=" * 70)
    print("SPRITE RENDERING TEST")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot to menu
    print("\nBooting to menu (500k cycles)...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    # Press START to get into game
    print("Pressing START to enter gameplay...")
    cpu.memory.joypad.press_button('start')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    # Run a bit more to get sprites on screen
    print("Running to get sprites on screen...")
    for _ in range(500_000):
        cpu.step()

    print(f"\nIn-game at {cpu.total_cycles:,} cycles")

    # Check sprite enable bit
    lcdc = cpu.memory.read_byte(0xFF40)
    sprite_enable = (lcdc >> 1) & 1
    print(f"\nLCDC: 0x{lcdc:02X}")
    print(f"  Sprite enable (bit 1): {sprite_enable} ({'ENABLED' if sprite_enable else 'DISABLED'})")

    if not sprite_enable:
        print("\n⚠️  WARNING: Sprites are disabled in LCDC!")
        print("  This is normal if game hasn't enabled them yet.")

    # Sample OAM to see if there are sprites
    print("\nOAM (Sprite) data sample (first 5 sprites):")
    cpu.memory._bypass_ppu_restrictions = True

    sprite_count = 0
    for i in range(5):
        oam_addr = 0xFE00 + (i * 4)
        y = cpu.memory.read_byte(oam_addr + 0)
        x = cpu.memory.read_byte(oam_addr + 1)
        tile = cpu.memory.read_byte(oam_addr + 2)
        flags = cpu.memory.read_byte(oam_addr + 3)

        # Adjust positions
        y_adj = y - 16
        x_adj = x - 8

        # Check if sprite is potentially visible
        is_visible = (0 <= y_adj < 144 and -7 <= x_adj < 160)

        print(f"  Sprite {i}: Y={y}({y_adj:+4d}), X={x}({x_adj:+4d}), Tile=0x{tile:02X}, Flags=0x{flags:02X} {'[VISIBLE]' if is_visible else ''}")

        if is_visible:
            sprite_count += 1

    print(f"\nVisible sprites found: {sprite_count}/5 (sampled)")

    # Check screen buffer for non-background colors
    print("\nAnalyzing screen buffer...")
    screen = cpu.ppu.get_screen_buffer()

    # Get background palette to know what colors BG uses
    bgp = cpu.memory.read_byte(0xFF47)
    obp0 = cpu.memory.read_byte(0xFF48)
    obp1 = cpu.memory.read_byte(0xFF49)

    print(f"Palettes:")
    print(f"  BGP:  0x{bgp:02X}")
    print(f"  OBP0: 0x{obp0:02X}")
    print(f"  OBP1: 0x{obp1:02X}")

    # Count colors
    color_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for row in screen:
        for pixel in row:
            color_counts[pixel] += 1

    total_pixels = 160 * 144
    print(f"\nScreen buffer color distribution:")
    for color in range(4):
        count = color_counts[color]
        pct = count * 100 / total_pixels
        print(f"  Color {color}: {count:5d} pixels ({pct:5.1f}%)")

    # Look for color changes that might indicate sprites
    if color_counts[0] < total_pixels * 0.9:
        print("\n✅ Screen has varied colors - likely has graphics!")
    else:
        print("\n⚠️  Screen is mostly one color")

    # Sample some scanlines to see variation
    print("\nSample scanlines (every 20 lines):")
    for y in range(0, 144, 20):
        colors = set(screen[y])
        print(f"  Line {y:3d}: {len(colors)} colors - {sorted(colors)}")

    # Try to detect sprites by looking for isolated color patches
    print("\nLooking for potential sprite patterns...")
    sprite_like_regions = 0

    for y in range(8, 136, 8):  # Sample every 8 lines
        for x in range(8, 152, 8):  # Sample every 8 pixels
            # Check if there's a color cluster (potential sprite)
            colors_in_region = set()
            for dy in range(min(8, 144 - y)):
                for dx in range(min(8, 160 - x)):
                    colors_in_region.add(screen[y + dy][x + dx])

            if len(colors_in_region) > 1:
                sprite_like_regions += 1

    print(f"  Regions with multiple colors: {sprite_like_regions} (out of {(136//8) * (152//8)} sampled)")

    if sprite_like_regions > 20:
        print("\n✅ Likely has sprites rendering!")
    elif sprite_like_regions > 5:
        print("\n⚠️  Some graphics, but maybe not many sprites")
    else:
        print("\n❌ Very few graphics - sprites may not be rendering")


def test_sprite_rendering_visual():
    """Create a simple ASCII visualization of sprites"""
    print("\n" + "=" * 70)
    print("SPRITE VISUALIZATION (ASCII)")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot and get into game
    while cpu.total_cycles < 500_000:
        cpu.step()

    cpu.memory.joypad.press_button('start')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('start')

    for _ in range(500_000):
        cpu.step()

    # Get screen buffer
    screen = cpu.ppu.get_screen_buffer()

    # Create ASCII art (downsample to fit terminal)
    print("\nScreen preview (downsampled 4x):")
    print("┌" + "─" * 40 + "┐")

    chars = [' ', '░', '▒', '█']  # Characters for colors 0-3

    for y in range(0, 144, 4):
        line = "│"
        for x in range(0, 160, 4):
            # Sample a 4x4 block
            avg_color = 0
            for dy in range(4):
                for dx in range(4):
                    if y + dy < 144 and x + dx < 160:
                        avg_color += screen[y + dy][x + dx]
            avg_color = avg_color // 16

            line += chars[min(avg_color, 3)]
        line += "│"
        print(line)

    print("└" + "─" * 40 + "┘")


if __name__ == '__main__':
    test_sprite_rendering()
    test_sprite_rendering_visual()
