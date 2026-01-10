"""Quick test to verify Gameboy Doctor integration works"""

import os
os.environ['GAMEBOY_DOCTOR'] = '1'

from src.cpu import CPU
from src.gameboy_doctor import initialize_cpu_for_doctor

print("Creating CPU in Gameboy Doctor mode...")
cpu = CPU()

print(f"Doctor logger active: {cpu._doctor_logger is not None}")

# Create a simple test ROM in memory
# NOP (0x00) at 0x100
cpu.memory.write_byte(0x0100, 0x00)  # NOP
cpu.memory.write_byte(0x0101, 0x3C)  # INC A
cpu.memory.write_byte(0x0102, 0x00)  # NOP
cpu.memory.write_byte(0x0103, 0x00)  # NOP

# Initialize to doctor state
initialize_cpu_for_doctor(cpu)

print(f"\nInitial state:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  A:  0x{cpu.registers._a:02X}")

# Execute a few instructions
print(f"\nExecuting 3 instructions...")
for i in range(3):
    cpu.step()
    print(f"  After step {i+1}: PC=0x{cpu.registers._pc:04X} A=0x{cpu.registers._a:02X}")

# Check the log file
print(f"\nChecking log file...")
try:
    with open("emulator_log.txt", "r") as f:
        lines = f.readlines()
    print(f"Log has {len(lines)} lines")
    print(f"\nFirst 3 log lines:")
    for i, line in enumerate(lines[:3]):
        print(f"  {i+1}: {line.strip()}")
    print("\nGameboy Doctor integration test: PASSED")
except Exception as e:
    print(f"ERROR reading log: {e}")
    print("Gameboy Doctor integration test: FAILED")
