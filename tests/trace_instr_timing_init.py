"""
Trace instr_timing.gb initialization to see where it fails
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
cpu.memory.load_rom_file('test_roms/instr_timing/instr_timing.gb')

print("Tracing until we see 'Timer doesn't' in serial output...")
print("="*80)

last_serial_len = 0

while cpu.total_cycles < 10_000_000:
    cpu.step()

    # Check serial output
    serial = cpu.memory.get_serial_output()
    if len(serial) > last_serial_len:
        new_chars = serial[last_serial_len:]
        last_serial_len = len(serial)

        # Check if we hit the error
        if "Timer" in new_chars or "doesn't" in serial:
            print(f"\nError detected at cycle {cpu.total_cycles:,}")
            print(f"Serial output so far: {serial}")
            print(f"\nCurrent state:")
            print(f"  PC: 0x{cpu.registers._pc:04X}")
            print(f"  A: 0x{cpu.registers._a:02X}")
            print(f"  DIV: 0x{cpu.memory.read_byte(0xFF04):02X}")
            print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
            print(f"  TMA: 0x{cpu.memory.read_byte(0xFF06):02X}")
            print(f"  TAC: 0x{cpu.memory.read_byte(0xFF07):02X}")
            print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
            print(f"  System counter: {cpu._system_counter}")

            # Trace back a bit to see what led to this
            print(f"\nLet me re-run and trace the last 100 instructions before the error...")
            break

if cpu.total_cycles >= 10_000_000:
    print("No error detected in 10M cycles")
