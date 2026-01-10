"""
Demonstration of PC logging fix

Shows the difference between PC before and after fetch,
and how the log correctly captures the PC before fetch.
"""

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
print("GAMEBOY DOCTOR - PC LOGGING FIX DEMONSTRATION")
print("=" * 70)

cpu = CPU()
initialize_cpu_for_doctor(cpu)

# Write some instructions at 0x0100
instructions = [
    (0x0100, 0x3C, "INC A"),       # PC will be 0x0100 before fetch
    (0x0101, 0x04, "INC B"),       # PC will be 0x0101 before fetch
    (0x0102, 0x0C, "INC C"),       # PC will be 0x0102 before fetch
]

for addr, opcode, name in instructions:
    cpu.memory.write_byte(addr, opcode)
    print(f"  0x{addr:04X}: {name} (opcode 0x{opcode:02X})")

print("\n" + "=" * 70)
print("EXECUTING INSTRUCTIONS")
print("=" * 70)

for i, (expected_pc, _, name) in enumerate(instructions, 1):
    pc_before = cpu.registers._pc
    a_before = cpu.registers._a
    b_before = cpu.registers._b
    c_before = cpu.registers._c

    cpu.step()

    pc_after = cpu.registers._pc
    a_after = cpu.registers._a
    b_after = cpu.registers._b
    c_after = cpu.registers._c

    print(f"\nStep {i}: {name}")
    print(f"  PC: 0x{pc_before:04X} → 0x{pc_after:04X}")
    print(f"  A={a_before:02X} B={b_before:02X} C={c_before:02X} → A={a_after:02X} B={b_after:02X} C={c_after:02X}")

print("\n" + "=" * 70)
print("LOG VERIFICATION")
print("=" * 70)

# Read log
with open("emulator_log.txt", "r") as f:
    log_lines = f.readlines()

print(f"\nGenerated {len(log_lines)} log lines:")
print()

expected_pcs = [0x0100, 0x0101, 0x0102]

all_correct = True
for i, (line, expected_pc) in enumerate(zip(log_lines, expected_pcs), 1):
    # Extract PC from log
    import re
    match = re.search(r'PC:([0-9A-F]{4})', line)
    if match:
        logged_pc = int(match.group(1), 16)
        status = "✅" if logged_pc == expected_pc else "❌"
        if logged_pc != expected_pc:
            all_correct = False

        print(f"{status} Log {i}: PC=0x{logged_pc:04X} (expected 0x{expected_pc:04X})")
    else:
        print(f"❌ Log {i}: Could not parse PC")
        all_correct = False

print("\n" + "=" * 70)
print("FULL LOG OUTPUT")
print("=" * 70)
print()

for i, line in enumerate(log_lines, 1):
    print(f"{i}: {line.strip()}")

print("\n" + "=" * 70)
if all_correct:
    print("✅ SUCCESS: All PCs logged correctly (before fetch)")
else:
    print("❌ FAILURE: Some PCs logged incorrectly")
print("=" * 70)
