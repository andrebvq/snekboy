"""
Trace VRAM writes from the very start
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

def trace_from_start():
    """Trace from the very beginning"""
    print("="*70)
    print("TRACING VRAM FROM START")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Intercept write_byte BEFORE we run anything
    vram_attempts = []
    lcdc_writes = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF:
            lcdc = cpu.memory._data[0xFF40]
            lcd_on = (lcdc & 0x80) != 0
            ppu_mode = cpu.ppu.current_mode if hasattr(cpu, 'ppu') else -1

            vram_attempts.append({
                'cycle': cpu.total_cycles,
                'pc': cpu.registers._pc,
                'address': address,
                'value': value,
                'lcd_on': lcd_on,
                'mode': ppu_mode
            })

        if address == 0xFF40:
            lcdc_writes.append((cpu.total_cycles, value, cpu.registers._pc))

        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run to 1M cycles
    print("\nRunning to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"\nResults after 1M cycles:")
    print(f"  VRAM writes: {len(vram_attempts)}")
    print(f"  LCDC writes: {len(lcdc_writes)}")

    if vram_attempts:
        print(f"\n  First 20 VRAM writes:")
        for i, attempt in enumerate(vram_attempts[:20]):
            lcd_status = "ON" if attempt['lcd_on'] else "OFF"
            print(f"    {i+1:2d}. Cycle {attempt['cycle']:8d}: PC=0x{attempt['pc']:04X} [0x{attempt['address']:04X}]=0x{attempt['value']:02X} LCD={lcd_status} Mode={attempt['mode']}")

    if lcdc_writes:
        print(f"\n  All LCDC writes:")
        for cycle, value, pc in lcdc_writes:
            lcd_on = "ON" if (value & 0x80) else "OFF"
            print(f"    Cycle {cycle:8d}: PC=0x{pc:04X} LCDC=0x{value:02X} LCD={lcd_on}")

    # Check screen
    screen = cpu.ppu.get_screen_buffer()
    pixels = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\n  Screen pixels: {pixels:,}")


if __name__ == '__main__':
    trace_from_start()
