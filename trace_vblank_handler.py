"""
Trace VBlank interrupt handler execution
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

def trace_vblank():
    """Trace VBlank interrupts and handler"""
    print("="*70)
    print("TRACING VBLANK INTERRUPTS")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"Reached {cpu.total_cycles:,} cycles")

    # Track VBlank interrupts
    vblank_count = 0
    handler_entries = []
    flag_writes = []

    original_step = cpu.step

    def traced_step():
        pc_before = cpu.registers._pc

        # Check if we're at VBlank vector
        if pc_before == 0x0040:
            nonlocal vblank_count
            vblank_count += 1
            handler_entries.append(cpu.total_cycles)

        result = original_step()

        # Check if 0xFF85 was written
        return result

    # Trace memory writes to 0xFF85
    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if address == 0xFF85:
            flag_writes.append((cpu.total_cycles, value, cpu.registers._pc))
        return original_write(address, value)

    cpu.step = traced_step
    cpu.memory.write_byte = traced_write

    # Run for a while
    print("\nRunning for 500k cycles...")
    start_cycles = cpu.total_cycles

    while cpu.total_cycles < start_cycles + 500_000:
        cpu.step()

    print(f"\nResults:")
    print(f"  VBlank vector entries (0x0040): {vblank_count}")
    print(f"  Flag writes (0xFF85): {len(flag_writes)}")

    if handler_entries:
        print(f"\n  First 5 VBlank handler calls:")
        for i, cycle in enumerate(handler_entries[:5]):
            print(f"    {i+1}. Cycle {cycle:,}")

    if flag_writes:
        print(f"\n  All flag writes:")
        for cycle, value, pc in flag_writes:
            print(f"    Cycle {cycle:8d}: PC=0x{pc:04X} wrote 0x{value:02X} to 0xFF85")
    else:
        print(f"\n  NO writes to 0xFF85 detected!")

    # Check interrupt state
    print(f"\nInterrupt state:")
    print(f"  IE (0xFFFF): 0x{cpu.memory.read_byte(0xFFFF):02X}")
    print(f"  IF (0xFF0F): 0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  IME (master): {cpu.ime}")

    # Check current flag value
    flag_value = cpu.memory.read_byte(0xFF85)
    print(f"  Current 0xFF85 value: 0x{flag_value:02X}")

    # Read VBlank handler code
    print(f"\nVBlank handler code at 0x0040:")
    for addr in range(0x0040, 0x0050):
        byte = cpu.memory.read_byte(addr)
        print(f"  0x{addr:04X}: 0x{byte:02X}")

    # Check if interrupts are enabled correctly
    ie = cpu.memory.read_byte(0xFFFF)
    if ie & 0x01:
        print(f"\n  VBlank interrupt is ENABLED (IE bit 0 = 1)")
    else:
        print(f"\n  VBlank interrupt is DISABLED (IE bit 0 = 0)")

    if cpu.ime:
        print(f"  Interrupt master enable is ON")
    else:
        print(f"  Interrupt master enable is OFF")


if __name__ == '__main__':
    trace_vblank()
