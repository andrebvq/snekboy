"""
Check what's in the OAM source data (0xC000)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def check_oam_source():
    """Check OAM source data"""
    print("="*70)
    print("OAM SOURCE DATA CHECK")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    print(f"\nAt {cpu.total_cycles:,} cycles")

    # Check OAM source at 0xC000
    print(f"\nOAM source data (0xC000-0xC09F):")

    for i in range(40):  # 40 sprites
        oam_addr = 0xC000 + (i * 4)
        y = cpu.memory.read_byte(oam_addr + 0)
        x = cpu.memory.read_byte(oam_addr + 1)
        tile = cpu.memory.read_byte(oam_addr + 2)
        flags = cpu.memory.read_byte(oam_addr + 3)

        # Only print non-zero sprites
        if y != 0 or x != 0 or tile != 0 or flags != 0:
            y_adj = y - 16
            x_adj = x - 8
            visible = (0 <= y_adj < 144 and -7 <= x_adj < 160)

            print(f"  Sprite {i:2d}: Y={y:3d}({y_adj:+4d}), X={x:3d}({x_adj:+4d}), Tile=0x{tile:02X}, Flags=0x{flags:02X} {'[VIS]' if visible else ''}")

    # Check actual OAM after DMA
    print(f"\nActual OAM (0xFE00-0xFE9F) after DMA:")

    cpu.memory._bypass_ppu_restrictions = True

    for i in range(40):
        oam_addr = 0xFE00 + (i * 4)
        y = cpu.memory.read_byte(oam_addr + 0)
        x = cpu.memory.read_byte(oam_addr + 1)
        tile = cpu.memory.read_byte(oam_addr + 2)
        flags = cpu.memory.read_byte(oam_addr + 3)

        if y != 0 or x != 0 or tile != 0 or flags != 0:
            y_adj = y - 16
            x_adj = x - 8
            visible = (0 <= y_adj < 144 and -7 <= x_adj < 160)

            print(f"  Sprite {i:2d}: Y={y:3d}({y_adj:+4d}), X={x:3d}({x_adj:+4d}), Tile=0x{tile:02X}, Flags=0x{flags:02X} {'[VIS]' if visible else ''}")

    cpu.memory._bypass_ppu_restrictions = False

    # Analysis
    print(f"\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # Count sprites in each location
    source_nonzero = sum(1 for i in range(160) if cpu.memory.read_byte(0xC000 + i) != 0)
    oam_nonzero = sum(1 for i in range(160) if cpu.memory.read_byte(0xFE00 + i) != 0)

    print(f"\nNon-zero bytes:")
    print(f"  Source (0xC000): {source_nonzero}/160")
    print(f"  OAM (0xFE00): {oam_nonzero}/160")

    if source_nonzero == oam_nonzero:
        print(f"  DMA is copying correctly!")
    else:
        print(f"  DMA copy mismatch!")


if __name__ == '__main__':
    check_oam_source()
