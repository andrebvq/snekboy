"""
Trace all attempts to write to VRAM, even blocked ones
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

def trace_vram_attempts():
    """Trace all VRAM write attempts"""
    print("="*70)
    print("TRACING VRAM WRITE ATTEMPTS (INCLUDING BLOCKED)")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"Reached {cpu.total_cycles:,} cycles")

    # Intercept write_byte BEFORE it checks restrictions
    vram_attempts = []
    vram_successful = []
    lcdc_values = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        # Track VRAM write attempts
        if 0x8000 <= address <= 0x9FFF:
            lcdc = cpu.memory._data[0xFF40]
            ppu_mode = cpu.ppu.current_mode if hasattr(cpu, 'ppu') else -1
            lcd_on = (lcdc & 0x80) != 0

            vram_attempts.append({
                'cycle': cpu.total_cycles,
                'pc': cpu.registers._pc,
                'address': address,
                'value': value,
                'lcdc': lcdc,
                'lcd_on': lcd_on,
                'mode': ppu_mode
            })

            # Call original to see if it goes through
            result = original_write(address, value)

            # Check if write succeeded
            if cpu.memory._data[address] == value:
                vram_successful.append(vram_attempts[-1])

            return result

        # Track LCDC changes
        if address == 0xFF40:
            lcdc_values.append((cpu.total_cycles, value, cpu.registers._pc))

        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run for a while
    print("\nRunning for 1M more cycles...")
    start_cycle = cpu.total_cycles

    while cpu.total_cycles < start_cycle + 1_000_000:
        cpu.step()

    # Results
    print(f"\nResults:")
    print(f"  VRAM write attempts: {len(vram_attempts)}")
    print(f"  VRAM writes successful: {len(vram_successful)}")
    print(f"  LCDC writes: {len(lcdc_values)}")

    if vram_attempts:
        print(f"\n  All VRAM write attempts:")
        for i, attempt in enumerate(vram_attempts[:20]):
            status = "SUCCESS" if attempt in vram_successful else "BLOCKED"
            lcd_status = "ON" if attempt['lcd_on'] else "OFF"
            print(f"    {i+1:2d}. Cycle {attempt['cycle']:8d}: PC=0x{attempt['pc']:04X} [0x{attempt['address']:04X}]=0x{attempt['value']:02X} LCD={lcd_status} Mode={attempt['mode']} {status}")
        if len(vram_attempts) > 20:
            print(f"    ... ({len(vram_attempts) - 20} more)")
    else:
        print(f"\n  NO VRAM write attempts detected!")
        print(f"  Game is not trying to write to VRAM at all!")

    if lcdc_values:
        print(f"\n  LCDC writes:")
        for cycle, value, pc in lcdc_values:
            lcd_on = "ON" if (value & 0x80) else "OFF"
            print(f"    Cycle {cycle:8d}: PC=0x{pc:04X} LCDC=0x{value:02X} LCD={lcd_on}")


if __name__ == '__main__':
    trace_vram_attempts()
