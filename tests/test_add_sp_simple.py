"""
Simple test of ADD SP,n
"""

from src.cpu import CPU

cpu = CPU()
cpu.registers._sp = 0x000F

print("Before ADD SP,n:")
print(f"  SP = 0x{cpu.registers._sp:04X}")

# Write instruction at PC location (0x0100)
cpu.memory._data[0x0100] = 0xE8  # ADD SP,n
cpu.memory._data[0x0101] = 0x01  # offset = +1

# Execute
cpu.step()

print(f"\nAfter ADD SP,n (+1):")
print(f"  SP = 0x{cpu.registers._sp:04X} (expected 0x0010)")
print(f"  Flags: Z={cpu.registers.flags.zero} N={cpu.registers.flags.subtract} H={cpu.registers.flags.half_carry} C={cpu.registers.flags.carry}")
print(f"  Expected: Z=False N=False H=True C=False")
