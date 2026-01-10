"""Test that initial state is logged before first instruction"""

import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

os.environ['GAMEBOY_DOCTOR'] = '1'

from src.cpu import CPU
from src.gameboy_doctor import initialize_cpu_for_doctor

# Clear log
with open("emulator_log.txt", "w") as f:
    f.write("")

print("=" * 70)
print("TEST: Initial State Logging")
print("=" * 70)

cpu = CPU()
initialize_cpu_for_doctor(cpu)

# Write INC A at 0x0100 (this will modify A and F flags)
cpu.memory.write_byte(0x0100, 0x3C)  # INC A

print(f"\nInitial state (before any execution):")
print(f"  A=0x{cpu.registers._a:02X}")
print(f"  F=0x{(cpu.registers.flags.zero << 7 | cpu.registers.flags.subtract << 6 | cpu.registers.flags.half_carry << 5 | cpu.registers.flags.carry << 4):02X}")
print(f"  PC=0x{cpu.registers._pc:04X}")

# Log initial state (simulating what run_gameboy_doctor.py does)
if cpu._doctor_logger:
    cpu._doctor_logger.log_step(cpu, cpu.registers._pc)
    print("\n✅ Logged initial state")

# Now execute one instruction
print(f"\nExecuting INC A...")
cpu.step()

print(f"\nState after INC A:")
print(f"  A=0x{cpu.registers._a:02X}")
print(f"  F=0x{(cpu.registers.flags.zero << 7 | cpu.registers.flags.subtract << 6 | cpu.registers.flags.half_carry << 5 | cpu.registers.flags.carry << 4):02X}")
print(f"  PC=0x{cpu.registers._pc:04X}")

# Read log
with open("emulator_log.txt", "r") as f:
    lines = f.readlines()

print(f"\n" + "=" * 70)
print(f"LOG VERIFICATION ({len(lines)} lines)")
print("=" * 70)

if len(lines) < 2:
    print("❌ FAILED: Expected at least 2 log lines")
else:
    print("\nLine 1 (Initial state - before INC A):")
    print(f"  {lines[0].strip()}")

    print("\nLine 2 (After INC A):")
    print(f"  {lines[1].strip()}")

    # Check line 1 has A:01 F:B0
    if "A:01" in lines[0] and "F:B0" in lines[0]:
        print("\n✅ Line 1: Correct initial state (A:01 F:B0)")
    else:
        print("\n❌ Line 1: Wrong initial state")

    # Check line 2 has A:02 (after INC)
    if "A:02" in lines[1]:
        print("✅ Line 2: Correct state after INC A (A:02)")
    else:
        print("❌ Line 2: Wrong state after INC A")

print("=" * 70)
