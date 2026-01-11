"""
Check VRAM state specifically when in gameplay (after pressing START)
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

def check_vram_progression():
    """Monitor VRAM content at different stages"""
    print("=" * 70)
    print("VRAM CONTENT PROGRESSION TEST")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    stages = [
        ("After ROM load", 0),
        ("After 100k cycles", 100_000),
        ("After 500k cycles (menu)", 500_000),
        ("After 1M cycles (pressed START)", 1_000_000),
        ("After 1.5M cycles (in game)", 1_500_000),
    ]

    for stage_name, target_cycles in stages:
        while cpu.total_cycles < target_cycles:
            cpu.step()

            # Simulate START press at 500k
            if cpu.total_cycles == 550_000:
                print("  [Pressing START]")
                cpu.memory.joypad.press_button('start')
            elif cpu.total_cycles == 600_000:
                cpu.memory.joypad.release_button('start')

        # Sample VRAM
        vram_sample = []
        for i in range(64):  # First 64 bytes
            vram_sample.append(cpu.memory.read_byte(0x8000 + i))

        # Count non-zero bytes in all VRAM
        vram_nonzero = 0
        for addr in range(0x8000, 0x9800):
            if cpu.memory.read_byte(addr) != 0:
                vram_nonzero += 1

        # Sample tile map
        tilemap_base = 0x9800  # BG map
        tilemap_sample = []
        for i in range(32):
            tilemap_sample.append(cpu.memory.read_byte(tilemap_base + i))

        tilemap_nonzero = 0
        for addr in range(0x9800, 0x9C00):
            val = cpu.memory.read_byte(addr)
            if val != 0 and val != 0xFF:
                tilemap_nonzero += 1

        print(f"\n{stage_name} ({cpu.total_cycles:,} cycles):")
        print(f"  LY: {cpu.memory.read_byte(0xFF44)}")
        print(f"  PPU Mode: {cpu.ppu.current_mode}")
        print(f"  VRAM non-zero bytes: {vram_nonzero}/6144 ({vram_nonzero*100/6144:.1f}%)")
        print(f"  Tile map non-zero/non-FF: {tilemap_nonzero}/1024")
        print(f"  VRAM[0x8000:0x8010]: " + " ".join(f"{b:02X}" for b in vram_sample[:16]))
        print(f"  Tilemap[0x9800:0x9810]: " + " ".join(f"{b:02X}" for b in tilemap_sample[:16]))


if __name__ == '__main__':
    check_vram_progression()
