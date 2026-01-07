"""
Test that DEC properly sets/clears the zero flag
"""

from src.cpu import CPU

cpu = CPU()

# Test 1: DEC when value is 1 should set zero flag
print("Test 1: DEC when value is 1")
cpu.registers._b = 1
cpu.registers.flags.zero = False
print(f"Before: B={cpu.registers._b}, Z={cpu.registers.flags.zero}")

# Manually execute DEC B (opcode 0x05)
cpu.memory.write_byte(0x0000, 0x05)  # DEC B
cpu.registers._pc = 0x0000
cpu.step()

print(f"After:  B={cpu.registers._b}, Z={cpu.registers.flags.zero}")
assert cpu.registers._b == 0, f"Expected B=0, got {cpu.registers._b}"
assert cpu.registers.flags.zero == True, f"Expected Z=True, got {cpu.registers.flags.zero}"
print("[PASS]\n")

# Test 2: DEC when value is 0 should clear zero flag (wraps to 255)
print("Test 2: DEC when value is 0 (wraps to 255)")
cpu.registers._b = 0
cpu.registers.flags.zero = True  # Start with zero flag set
print(f"Before: B={cpu.registers._b}, Z={cpu.registers.flags.zero}")

cpu.memory.write_byte(0x0100, 0x05)  # DEC B
cpu.registers._pc = 0x0100
cpu.step()

print(f"After:  B={cpu.registers._b}, Z={cpu.registers.flags.zero}")
assert cpu.registers._b == 255, f"Expected B=255, got {cpu.registers._b}"
assert cpu.registers.flags.zero == False, f"Expected Z=False when B=255, got {cpu.registers.flags.zero}"
print("[PASS]\n")

# Test 3: DEC when value is 2 should keep zero flag clear
print("Test 3: DEC when value is 2")
cpu.registers._b = 2
cpu.registers.flags.zero = False
print(f"Before: B={cpu.registers._b}, Z={cpu.registers.flags.zero}")

cpu.memory.write_byte(0x0200, 0x05)  # DEC B
cpu.registers._pc = 0x0200
cpu.step()

print(f"After:  B={cpu.registers._b}, Z={cpu.registers.flags.zero}")
assert cpu.registers._b == 1, f"Expected B=1, got {cpu.registers._b}"
assert cpu.registers.flags.zero == False, f"Expected Z=False, got {cpu.registers.flags.zero}"
print("[PASS]\n")

print("="*60)
print("All DEC zero flag tests passed!")
