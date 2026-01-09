"""
Test ADD HL,SP with boundary values to check Z/H/C flags
This checks point #3 from the analysis
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def get_f_register(flags):
    f = 0
    if flags.zero: f |= 0x80
    if flags.subtract: f |= 0x40
    if flags.half_carry: f |= 0x20
    if flags.carry: f |= 0x10
    return f

def test_add_hl_sp():
    cpu = CPU()

    print("Testing ADD HL,SP with boundary values")
    print("=" * 80)

    # Important: According to Game Boy manual, ADD HL,rr does NOT set Z flag!
    # Z is preserved (unchanged), N is reset to 0, H and C are set based on carries

    # Test 1: HL=$0001 + SP=$FFFF = $10000 (wraps to $0000)
    # Result should be $0000, but Z should be PRESERVED (not set to 1)
    # C should be 1 (carry from bit 15)
    # H should be 1 (carry from bit 11)
    print("\nTest 1: ADD HL,SP with HL=$0001, SP=$FFFF")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0x0001
    cpu.registers._sp = 0xFFFF
    cpu.registers.flags.zero = False  # Z should be preserved
    cpu.step()

    print(f"  HL before: 0x0001, SP: 0xFFFF")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (expected 0x0000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, PRESERVED)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers.hl == 0x0000, f"HL should be 0x0000, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == False, "Z should be PRESERVED (0), not set to 1!"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == True, "H should be 1"
    assert cpu.registers.flags.carry == True, "C should be 1"
    print("  PASS")

    # Test 2: Same but with Z=1 initially (should stay 1)
    print("\nTest 2: ADD HL,SP with HL=$0001, SP=$FFFF, initial Z=1")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0x0001
    cpu.registers._sp = 0xFFFF
    cpu.registers.flags.zero = True  # Z should be preserved
    cpu.step()

    print(f"  HL before: 0x0001, SP: 0xFFFF")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (expected 0x0000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 1, PRESERVED)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers.hl == 0x0000
    assert cpu.registers.flags.zero == True, "Z should be PRESERVED (1)!"
    assert cpu.registers.flags.subtract == False
    assert cpu.registers.flags.half_carry == True
    assert cpu.registers.flags.carry == True
    print("  PASS")

    # Test 3: HL=$8000 + SP=$8000 = $10000 (wraps to $0000)
    print("\nTest 3: ADD HL,SP with HL=$8000, SP=$8000")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0x8000
    cpu.registers._sp = 0x8000
    cpu.registers.flags.zero = False
    cpu.step()

    print(f"  HL before: 0x8000, SP: 0x8000")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (expected 0x0000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 0, no carry from bit 11)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers.hl == 0x0000
    assert cpu.registers.flags.zero == False, "Z preserved"
    assert cpu.registers.flags.subtract == False
    assert cpu.registers.flags.half_carry == False, "H should be 0 (no carry from bit 11)"
    assert cpu.registers.flags.carry == True
    print("  PASS")

    # Test 4: No overflow case
    print("\nTest 4: ADD HL,SP with HL=$1000, SP=$2000 (no overflow)")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0x1000
    cpu.registers._sp = 0x2000
    cpu.registers.flags.zero = True
    cpu.step()

    print(f"  HL before: 0x1000, SP: 0x2000")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (expected 0x3000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 1, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 0)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 0)")

    assert cpu.registers.hl == 0x3000
    assert cpu.registers.flags.zero == True, "Z preserved"
    assert cpu.registers.flags.subtract == False
    assert cpu.registers.flags.half_carry == False
    assert cpu.registers.flags.carry == False
    print("  PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("ADD HL,SP correctly preserves Z and sets H/C flags")
    print("=" * 80)

if __name__ == "__main__":
    test_add_hl_sp()
