"""
Test DIV calculation from system counter
"""

from src.cpu import CPU

cpu = CPU()

print("Testing DIV calculation...")
print("="*80)

# Test at various system counter values
test_values = [
    (0, 0),
    (255, 0),
    (256, 1),
    (512, 2),
    (64676, 252),  # From the error trace: 64676 / 256 = 252.64, so DIV should be 252 (0xFC)
]

for sys_counter, expected_div in test_values:
    # Manually set system counter for testing
    cpu._system_counter = sys_counter

    # Trigger a timer update to update DIV
    cpu._update_timers(1)

    actual_div = cpu.memory.read_byte(0xFF04)
    calculated_div = (sys_counter // 256) & 0xFF

    status = "[PASS]" if actual_div == expected_div else "[FAIL]"
    print(f"{status} sys_counter={sys_counter:5d} -> DIV: expected=0x{expected_div:02X}, actual=0x{actual_div:02X}, calc=0x{calculated_div:02X}")

# Also test DIV write (should reset to 0)
print("\nTesting DIV write (should reset system counter)...")
cpu._system_counter = 1000
cpu.memory.write_byte(0xFF04, 0x55)  # Writing ANY value should reset
div_after = cpu.memory.read_byte(0xFF04)
sys_after = cpu._system_counter

print(f"  After writing 0x55 to DIV:")
print(f"  DIV: 0x{div_after:02X} (expected 0x00)")
print(f"  System counter: {sys_after} (expected 0)")

if div_after == 0 and sys_after == 0:
    print("  [PASS]")
else:
    print("  [FAIL]")
