"""
Verify DIV increments at exactly 16384 Hz (every 256 T-cycles)
"""

from src.cpu import CPU

cpu = CPU()

print("Testing DIV frequency")
print("="*80)

initial_div = cpu.memory.read_byte(0xFF04)
print(f"Initial DIV: 0x{initial_div:02X}")
print(f"Initial system counter: {cpu._system_counter}")

# Run for exactly 256 T-cycles (64 M-cycles)
for i in range(64):
    cpu.step()

final_div = cpu.memory.read_byte(0xFF04)
final_counter = cpu._system_counter

print(f"\nAfter 256 T-cycles:")
print(f"  DIV: 0x{final_div:02X}")
print(f"  System counter: {final_counter}")
print(f"  Expected DIV: 0x{(initial_div + 1) & 0xFF:02X}")

if final_div == (initial_div + 1) & 0xFF:
    print("\n[PASS] DIV increments exactly every 256 T-cycles")
else:
    print(f"\n[FAIL] DIV should be {(initial_div + 1) & 0xFF}, got {final_div}")

# Test the frequency matches 16384 Hz
print("\n" + "="*80)
print("Verifying 16384 Hz frequency:")
print(f"  CPU clock: 4194304 Hz")
print(f"  DIV freq: 4194304 / 256 = {4194304 // 256} Hz")
print(f"  Expected: 16384 Hz")

if 4194304 // 256 == 16384:
    print("  [PASS] Frequency calculation correct")

# Also verify that our system counter approach gives the same result
print("\n" + "="*80)
print("Testing DIV calculation formula:")
print(f"  System counter after 256 T-cycles: {final_counter}")
print(f"  DIV = system_counter // 256 = {final_counter} // 256 = {final_counter // 256}")
print(f"  Actual DIV value: {final_div}")

if final_counter // 256 == final_div:
    print("  [PASS] DIV calculation formula correct")
else:
    print(f"  [FAIL] Formula gives {final_counter // 256}, actual is {final_div}")
