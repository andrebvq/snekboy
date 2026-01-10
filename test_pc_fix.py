"""Test that PC is logged correctly (before fetch, not after)"""

import os
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

os.environ['GAMEBOY_DOCTOR'] = '1'

from src.cpu import CPU
from src.gameboy_doctor import initialize_cpu_for_doctor

print("Testing PC logging fix...")

# Clear log
with open("emulator_log.txt", "w") as f:
    f.write("")

cpu = CPU()
initialize_cpu_for_doctor(cpu)

# Write a NOP instruction at 0x0100
cpu.memory.write_byte(0x0100, 0x00)  # NOP

print(f"\nBefore step:")
print(f"  PC: 0x{cpu.registers._pc:04X}")

# Execute one instruction
cpu.step()

print(f"\nAfter step:")
print(f"  PC: 0x{cpu.registers._pc:04X}")

# Check log
with open("emulator_log.txt", "r") as f:
    log_line = f.read().strip()

print(f"\nLog line:")
print(f"  {log_line}")

# Extract PC from log
import re
match = re.search(r'PC:([0-9A-F]{4})', log_line)
if match:
    logged_pc = match.group(1)
    print(f"\nPC in log: 0x{logged_pc}")

    if logged_pc == "0100":
        print("✅ CORRECT: PC logged as 0x0100 (before fetch)")
    else:
        print(f"❌ WRONG: PC logged as 0x{logged_pc} (expected 0x0100)")
else:
    print("❌ ERROR: Could not parse PC from log")

# Also check PCMEM is from current PC (0x0101)
match_pcmem = re.search(r'PCMEM:([0-9A-F,]+)', log_line)
if match_pcmem:
    pcmem = match_pcmem.group(1)
    print(f"\nPCMEM in log: {pcmem}")
    print(f"(This should be the bytes at PC=0x0101, the current PC after execution)")
