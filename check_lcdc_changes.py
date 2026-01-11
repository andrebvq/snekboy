"""
Check how LCDC changes during boot and gameplay
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

def check_lcdc():
    """Track LCDC changes"""
    print("="*70)
    print("TRACKING LCDC REGISTER CHANGES")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    print(f"\nAfter boot ROM simulation:")
    lcdc = cpu.memory.read_byte(0xFF40)
    print(f"  LCDC = 0x{lcdc:02X} = 0b{lcdc:08b}")
    print(f"    Bit 7 (LCD on): {(lcdc >> 7) & 1}")
    print(f"    Bit 6 (Window tilemap): {(lcdc >> 6) & 1}")
    print(f"    Bit 5 (Window on): {(lcdc >> 5) & 1}")
    print(f"    Bit 4 (BG/Window tiles): {(lcdc >> 4) & 1}")
    print(f"    Bit 3 (BG tilemap): {(lcdc >> 3) & 1}")
    print(f"    Bit 2 (Sprite size): {(lcdc >> 2) & 1}")
    print(f"    Bit 1 (Sprite on): {(lcdc >> 1) & 1}")
    print(f"    Bit 0 (BG on): {(lcdc >> 0) & 1}")

    # Track writes to LCDC
    lcdc_writes = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if address == 0xFF40:
            lcdc_writes.append((cpu.total_cycles, value, cpu.registers._pc))
        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run to 2M cycles
    print(f"\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    print(f"\nLCDC writes detected: {len(lcdc_writes)}")

    if lcdc_writes:
        print(f"\nAll LCDC writes:")
        for cycle, value, pc in lcdc_writes:
            print(f"  Cycle {cycle:8d}: PC=0x{pc:04X} wrote 0x{value:02X} = 0b{value:08b}")

    # Show final LCDC value
    final_lcdc = cpu.memory.read_byte(0xFF40)
    print(f"\nFinal LCDC = 0x{final_lcdc:02X} = 0b{final_lcdc:08b}")
    print(f"    Bit 7 (LCD on): {(final_lcdc >> 7) & 1}")
    print(f"    Bit 6 (Window tilemap): {(final_lcdc >> 6) & 1}")
    print(f"    Bit 5 (Window on): {(final_lcdc >> 5) & 1}")
    print(f"    Bit 4 (BG/Window tiles): {(final_lcdc >> 4) & 1}")
    print(f"    Bit 3 (BG tilemap): {(final_lcdc >> 3) & 1}")
    print(f"    Bit 2 (Sprite size): {(final_lcdc >> 2) & 1}")
    print(f"    Bit 1 (Sprite on): {(final_lcdc >> 1) & 1}")
    print(f"    Bit 0 (BG on): {(final_lcdc >> 0) & 1}")

    # Compare with real Game Boy boot ROM value
    print(f"\nExpected after real boot ROM: 0x91 = 0b10010001")
    print(f"  (LCD on, BG tilemap 0x9800, BG tiles 0x8000, Sprites on, BG on)")

    # Check if this matches
    if final_lcdc == 0x91:
        print(f"\n  MATCHES real boot ROM!")
    else:
        print(f"\n  DIFFERS from real boot ROM!")
        print(f"  Game has changed LCDC")


if __name__ == '__main__':
    check_lcdc()
