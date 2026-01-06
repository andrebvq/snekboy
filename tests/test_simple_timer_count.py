"""
Simple test: run exactly 16 T-cycles and count TIMA increments
"""

from src.cpu import CPU

cpu = CPU()

# Configure for 262144 Hz (every 16 T-cycles)
cpu.memory.write_byte(0xFF06, 0x00)
cpu.memory.write_byte(0xFF05, 0x00)
cpu.memory.write_byte(0xFF07, 0x05)

print(f"Initial TIMA: {cpu.memory.read_byte(0xFF05)}")
print(f"Running exactly 4 M-cycles (16 T-cycles)...")

# 4 M-cycles = 16 T-cycles
cpu.step()
cpu.step()
cpu.step()
cpu.step()

tima = cpu.memory.read_byte(0xFF05)
print(f"Final TIMA: {tima}")
print(f"Total T-cycles: {cpu.total_cycles}")

if tima == 1:
    print("[PASS]")
else:
    print(f"[FAIL] Expected 1, got {tima}")
