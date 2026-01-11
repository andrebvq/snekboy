"""
Debug why Tetris gets stuck after stage selection
Track exactly what happens during menu navigation
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

def analyze_screen_state(cpu, label):
    """Analyze what's on screen and PPU state"""
    print(f"\n{'='*70}")
    print(f"{label}")
    print(f"{'='*70}")
    print(f"Total cycles: {cpu.total_cycles:,}")

    # PPU state
    lcdc = cpu.memory.read_byte(0xFF40)
    stat = cpu.memory.read_byte(0xFF41)
    scy = cpu.memory.read_byte(0xFF42)
    scx = cpu.memory.read_byte(0xFF43)
    ly = cpu.memory.read_byte(0xFF44)

    print(f"\nPPU State:")
    print(f"  LCDC: 0x{lcdc:02X} (LCD {'ON' if lcdc & 0x80 else 'OFF'})")
    print(f"  LCD Enable: {bool(lcdc & 0x80)}")
    print(f"  BG Enable: {bool(lcdc & 0x01)}")
    print(f"  Sprite Enable: {bool(lcdc & 0x02)}")
    print(f"  BG Tile Map: 0x{'9C00' if lcdc & 0x08 else '9800'}")
    print(f"  BG Tile Data: 0x{'8000' if lcdc & 0x10 else '8800'}")
    print(f"  Scroll: SCY={scy}, SCX={scx}")
    print(f"  LY: {ly}")

    # Check interrupts
    ie = cpu.memory.read_byte(0xFFFF)
    if_flag = cpu.memory.read_byte(0xFF0F)
    ime = cpu.ime

    print(f"\nInterrupt State:")
    print(f"  IME: {ime}")
    print(f"  IE:  0x{ie:02X} (VBlank={bool(ie&1)}, LCD={bool(ie&2)}, Timer={bool(ie&4)}, Serial={bool(ie&8)}, Joypad={bool(ie&16)})")
    print(f"  IF:  0x{if_flag:02X} (VBlank={bool(if_flag&1)}, LCD={bool(if_flag&2)}, Timer={bool(if_flag&4)}, Serial={bool(if_flag&8)}, Joypad={bool(if_flag&16)})")

    # Joypad state
    joyp = cpu.memory.read_byte(0xFF00)
    print(f"\nJoypad:")
    print(f"  P1/JOYP: 0x{joyp:02X}")

    # Sample screen
    screen = cpu.ppu.get_screen_buffer()

    # Count unique colors
    color_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for row in screen:
        for pixel in row:
            color_counts[pixel] += 1

    print(f"\nScreen buffer:")
    for color in range(4):
        pct = color_counts[color] * 100 / 23040
        print(f"  Color {color}: {color_counts[color]:5d} pixels ({pct:5.1f}%)")

    # Show a small ASCII preview of top-left corner
    print(f"\nTop-left corner (32x32 pixels):")
    chars = [' ', '░', '▒', '█']
    for y in range(0, 32, 2):
        line = ""
        for x in range(0, 32, 1):
            line += chars[screen[y][x]]
        print(f"  {line}")

    # Check if screen is "stuck" showing just stripes
    # Count horizontal variation
    stripe_lines = 0
    for y in range(144):
        colors_in_line = set(screen[y])
        if len(colors_in_line) <= 2:  # Very little variation
            stripe_lines += 1

    print(f"\nScreen analysis:")
    print(f"  Lines with minimal variation: {stripe_lines}/144")
    if stripe_lines > 120:
        print(f"  ⚠️  Screen appears to show mostly uniform pattern (stripes)")


def test_stage_selection():
    """Simulate stage selection and see what happens"""
    print("="*70)
    print("TETRIS STAGE SELECTION DEBUG")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Stage 1: Boot to title screen
    print("\n[Stage 1: Booting to title screen]")
    while cpu.total_cycles < 500_000:
        cpu.step()

    analyze_screen_state(cpu, "After boot (title screen)")

    # Stage 2: Press START to enter mode selection
    print("\n[Stage 2: Pressing START to enter mode selection]")
    cpu.memory.joypad.press_button('start')

    # Hold for a bit
    for _ in range(10_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    # Let game process the input
    for _ in range(100_000):
        cpu.step()

    analyze_screen_state(cpu, "After first START press (mode selection)")

    # Stage 3: Press START again to select mode and start game
    print("\n[Stage 3: Pressing START again to start game]")
    cpu.memory.joypad.press_button('start')

    for _ in range(10_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    # Let game load
    for _ in range(200_000):
        cpu.step()

    analyze_screen_state(cpu, "After second START press (should be in game)")

    # Stage 4: Wait even longer - maybe it takes time to set up
    print("\n[Stage 4: Waiting longer for game to fully load]")
    for _ in range(500_000):
        cpu.step()

    analyze_screen_state(cpu, "After waiting 500k more cycles")

    # Stage 5: Try pressing other buttons to see if game is responsive
    print("\n[Stage 5: Testing if game responds to input]")

    # Try moving left
    cpu.memory.joypad.press_button('left')
    for _ in range(50_000):
        cpu.step()
    cpu.memory.joypad.release_button('left')

    for _ in range(50_000):
        cpu.step()

    analyze_screen_state(cpu, "After pressing LEFT")

    # Check if VRAM has gameplay graphics
    print("\n[Checking VRAM for gameplay graphics]")
    cpu.memory._bypass_ppu_restrictions = True

    # Sample some tile data
    print("\nTile data samples:")
    for tile_num in [0x00, 0x01, 0x02, 0x10, 0x20, 0x30]:
        addr = 0x8000 + (tile_num * 16)
        tile_bytes = [cpu.memory.read_byte(addr + i) for i in range(16)]

        # Check if tile has actual graphics
        non_zero = sum(1 for b in tile_bytes if b != 0x00 and b != 0xFF)

        sample = " ".join(f"{b:02X}" for b in tile_bytes[:8])
        print(f"  Tile 0x{tile_num:02X}: {sample}... (non-trivial bytes: {non_zero}/16)")

    # Sample tile map
    print("\nTile map (BG Map 0) sample:")
    for row in range(4):
        addr = 0x9800 + (row * 32)
        tiles = [cpu.memory.read_byte(addr + i) for i in range(32)]
        tile_str = " ".join(f"{t:02X}" for t in tiles[:16])
        print(f"  Row {row}: {tile_str}...")

    # Sample OAM
    print("\nOAM (first 5 sprites):")
    for i in range(5):
        oam_addr = 0xFE00 + (i * 4)
        y = cpu.memory.read_byte(oam_addr + 0)
        x = cpu.memory.read_byte(oam_addr + 1)
        tile = cpu.memory.read_byte(oam_addr + 2)
        flags = cpu.memory.read_byte(oam_addr + 3)

        y_adj = y - 16
        x_adj = x - 8

        visible = (0 <= y_adj < 144 and -7 <= x_adj < 160)

        print(f"  Sprite {i}: Y={y:3d}({y_adj:+4d}), X={x:3d}({x_adj:+4d}), Tile=0x{tile:02X}, Flags=0x{flags:02X} {'[VIS]' if visible else ''}")


if __name__ == '__main__':
    test_stage_selection()
