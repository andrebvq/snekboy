"""
Check VRAM very early in boot to see when graphics are loaded
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

def check_early_vram():
    """Check VRAM very early during boot"""
    print("=" * 70)
    print("EARLY VRAM MONITORING")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    checkpoints = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000, 500_000]

    for checkpoint in checkpoints:
        while cpu.total_cycles < checkpoint:
            cpu.step()

        # Quick VRAM check
        vram_sample = []
        for i in range(16):
            vram_sample.append(cpu.memory.read_byte(0x8000 + i))

        sample_str = " ".join(f"{b:02X}" for b in vram_sample)

        # Count non-zero and non-FF
        vram_useful = 0
        for addr in range(0x8000, 0x9800):
            val = cpu.memory.read_byte(addr)
            if val != 0 and val != 0xFF:
                vram_useful += 1

        print(f"\n{checkpoint//1000:3d}k cycles:")
        print(f"  VRAM[0x8000]: {sample_str}")
        print(f"  VRAM useful bytes (not 0 or FF): {vram_useful}/6144")

        if vram_useful > 100:
            print(f"  ✅ Graphics data found!")
            # Show where it is
            for addr in range(0x8000, 0x9800, 16):
                line = []
                for i in range(16):
                    val = cpu.memory.read_byte(addr + i)
                    line.append(val)

                if any(v != 0 and v != 0xFF for v in line):
                    line_str = " ".join(f"{b:02X}" for b in line)
                    print(f"    0x{addr:04X}: {line_str}")
                    if len([v for v in line if v != 0 and v != 0xFF]) >= 8:
                        break  # Just show a few lines

if __name__ == '__main__':
    check_early_vram()
