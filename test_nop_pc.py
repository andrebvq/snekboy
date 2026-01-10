"""Test that PC increments correctly after NOP"""

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
print("TEST: NOP PC Increment")
print("=" * 70)

cpu = CPU()
initialize_cpu_for_doctor(cpu)

# Write NOP at 0x0100
cpu.memory.write_byte(0x0100, 0x00)  # NOP

print(f"\nBefore execution:")
print(f"  PC=0x{cpu.registers._pc:04X}")

# Log initial state
cpu._doctor_logger.log_step(cpu)
print(f"  ✅ Logged initial state (PC should be 0x0100)")

# Execute NOP
cpu.step()

print(f"\nAfter NOP:")
print(f"  PC=0x{cpu.registers._pc:04X} (should be 0x0101)")

# Check log
with open("emulator_log.txt", "r") as f:
    lines = f.readlines()

print(f"\n" + "=" * 70)
print(f"LOG VERIFICATION")
print("=" * 70)

print(f"\nLine 1 (initial state):")
print(f"  {lines[0].strip()}")
if "PC:0100" in lines[0]:
    print("  ✅ PC:0100 correct")
else:
    print("  ❌ PC should be 0100")

print(f"\nLine 2 (after NOP):")
print(f"  {lines[1].strip()}")
if "PC:0101" in lines[1]:
    print("  ✅ PC:0101 correct (NOP incremented PC)")
else:
    print("  ❌ PC should be 0101 after NOP")

print("=" * 70)
