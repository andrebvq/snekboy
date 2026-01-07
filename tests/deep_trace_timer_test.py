"""
Deep trace of what happens during the timer test in instr_timing
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
cpu.memory.load_rom_file('test_roms/instr_timing/instr_timing.gb')

print("Running until we hit the test_timer function...")
print("="*80)

# Run until we get to test_timer or see output
while cpu.total_cycles < 10_000_000:
    pc = cpu.registers._pc

    # Check if we're calling start_timer (likely around 0xC5XX based on common structure)
    # Or check for writes to timer registers

    # Look for the pattern: write to TIMA, write to TAC
    if pc == 0xC000:  # Entry point to test code in RAM
        print(f"\nReached RAM execution at cycle {cpu.total_cycles:,}")
        print(f"Timer registers:")
        print(f"  TAC: 0x{cpu.memory.read_byte(0xFF07):02X}")
        print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
        print(f"  TMA: 0x{cpu.memory.read_byte(0xFF06):02X}")
        print(f"  DIV: 0x{cpu.memory.read_byte(0xFF04):02X}")

    cpu.step()

    # Check if we just wrote to TAC to enable timer
    if cpu.memory.read_byte(0xFF07) == 0x05:
        # Timer is now enabled, let's trace carefully
        pass

    # Check serial output
    serial = cpu.memory.get_serial_output()
    if "Timer" in serial:
        print(f"\n'Timer' appeared in output at cycle {cpu.total_cycles:,}")
        print(f"Full output: {serial}")
        print(f"\nTimer state when error detected:")
        print(f"  TAC: 0x{cpu.memory.read_byte(0xFF07):02X}")
        print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
        print(f"  TMA: 0x{cpu.memory.read_byte(0xFF06):02X}")
        print(f"  DIV: 0x{cpu.memory.read_byte(0xFF04):02X}")
        print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
        print(f"  System counter: {cpu._system_counter}")
        print(f"  A register: 0x{cpu.registers._a:02X}")
        break

# Let's also try to understand what the exact failure is
# by checking if the timer increments properly from a known state

print("\n" + "="*80)
print("Let me test the timer behavior in isolation...")
print("="*80)

cpu2 = CPU()

# Set up timer exactly like Blargg does
cpu2.memory.write_byte(0xFFFF, cpu2.memory.read_byte(0xFFFF) & ~0x04)  # Disable timer interrupt in IE
cpu2.memory.write_byte(0xFF06, 0x00)  # TMA = 0
cpu2.memory.write_byte(0xFF07, 0x05)  # TAC = 0x05 (enable, 262144 Hz)

# Test: set TIMA to -20 (0xEC), delay 70 cycles, check IF
print("\nTest 1: TIMA overflow timing")
print("  Setting TIMA=0xEC, delaying 70 T-cycles...")
cpu2.memory.write_byte(0xFF0F, 0x00)  # Clear IF
cpu2.memory.write_byte(0xFF05, 0xEC)  # TIMA = -20

initial_tima = cpu2.memory.read_byte(0xFF05)
initial_cycles = cpu2.total_cycles

# Delay 70 T-cycles (17.5 M-cycles, so 18 M-cycles)
for _ in range(18):
    cpu2.step()

final_tima = cpu2.memory.read_byte(0xFF05)
final_if = cpu2.memory.read_byte(0xFF0F)

print(f"  Initial TIMA: 0x{initial_tima:02X}")
print(f"  After 72 T-cycles: TIMA=0x{final_tima:02X}, IF=0x{final_if:02X}")
print(f"  Expected: TIMA should be around 0xEC+4=0xF0, IF should be 0x00 (no overflow yet)")

if (final_if & 0x04) == 0:
    print("  [PASS] Timer did not overflow yet")
else:
    print("  [FAIL] Timer overflowed too early")

# Continue a bit more to see when overflow happens
print("\n  Continuing to see when overflow occurs...")
for i in range(20):
    cpu2.step()
    tima = cpu2.memory.read_byte(0xFF05)
    if_reg = cpu2.memory.read_byte(0xFF0F)

    if (if_reg & 0x04) != 0:
        print(f"  Overflow at T-cycle {cpu2.total_cycles} (delta={cpu2.total_cycles - initial_cycles})")
        print(f"  TIMA after overflow: 0x{tima:02X}")
        break
