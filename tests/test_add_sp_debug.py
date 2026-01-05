"""
Debug ADD SP,n execution step by step
"""

from src.cpu import CPU

cpu = CPU()
cpu.registers._sp = 0x000F

print("Before ADD SP,n:")
print(f"  SP = 0x{cpu.registers._sp:04X}")
print(f"  PC = 0x{cpu.registers._pc:04X}")

# Write instruction at PC location (0x0100)
cpu.memory._data[0x0100] = 0xE8  # ADD SP,n
cpu.memory._data[0x0101] = 0x01  # offset = +1

# Check what decode returns
pc_before = cpu.registers._pc
opcode = cpu.memory.read_byte(pc_before)
print(f"\nOpcode at PC=0x{pc_before:04X}: 0x{opcode:02X}")

# Decode
from src.cpu_decoder import decode_instruction, InstructionType

pc_val = [1]  # Use list to allow modification in nested function
def fetch():
    val = cpu.memory.read_byte(cpu.registers._pc + pc_val[0])
    pc_val[0] += 1
    return val

instr_type, target, immediate = decode_instruction(opcode, fetch)
print(f"Decoded: type={instr_type}, target={target}, immediate={immediate}")

# Now step
print("\nStepping...")
cpu.step()

print(f"\nAfter ADD SP,n:")
print(f"  SP = 0x{cpu.registers._sp:04X} (expected 0x0010)")
print(f"  PC = 0x{cpu.registers._pc:04X}")
print(f"  Z={cpu.registers.flags.zero} N={cpu.registers.flags.subtract} H={cpu.registers.flags.half_carry} C={cpu.registers.flags.carry}")
