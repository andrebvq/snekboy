"""
Test flag handling for INC/DEC SP and ADD HL,SP with initial flags set
This checks points #2 and #3 from the analysis
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

def test_sp_flags():
    cpu = CPU()

    print("Testing flag handling for INC SP, DEC SP, and ADD HL,SP")
    print("=" * 80)

    # Point #3: INC SP (0x33) should leave ALL flags unchanged
    print("\nTest 1: INC SP with initial F=$F0 (all flags set)")
    cpu.memory.write_byte(0x0000, 0x33)  # INC SP
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    # Set all flags to 1
    cpu.registers.flags.zero = True
    cpu.registers.flags.subtract = True
    cpu.registers.flags.half_carry = True
    cpu.registers.flags.carry = True
    f_before = get_f_register(cpu.registers.flags)

    cpu.step()
    f_after = get_f_register(cpu.registers.flags)

    print(f"  SP before: 0xDFF0, after: 0x{cpu.registers._sp:04X} (should be 0xDFF1)")
    print(f"  F before: 0x{f_before:02X}, after: 0x{f_after:02X} (should be unchanged)")
    print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

    assert cpu.registers._sp == 0xDFF1
    assert f_after == f_before, f"F should be unchanged, was 0x{f_before:02X}, now 0x{f_after:02X}"
    assert cpu.registers.flags.zero == True, "Z should be unchanged"
    assert cpu.registers.flags.subtract == True, "N should be unchanged"
    assert cpu.registers.flags.half_carry == True, "H should be unchanged"
    assert cpu.registers.flags.carry == True, "C should be unchanged"
    print("  PASS")

    # Test 2: INC SP with initial F=$00 (all flags clear)
    print("\nTest 2: INC SP with initial F=$00 (all flags clear)")
    cpu.memory.write_byte(0x0000, 0x33)  # INC SP
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = False
    cpu.registers.flags.subtract = False
    cpu.registers.flags.half_carry = False
    cpu.registers.flags.carry = False
    f_before = get_f_register(cpu.registers.flags)

    cpu.step()
    f_after = get_f_register(cpu.registers.flags)

    print(f"  SP before: 0xDFF0, after: 0x{cpu.registers._sp:04X} (should be 0xDFF1)")
    print(f"  F before: 0x{f_before:02X}, after: 0x{f_after:02X} (should be unchanged)")

    assert cpu.registers._sp == 0xDFF1
    assert f_after == f_before, f"F should be unchanged"
    assert cpu.registers.flags.zero == False
    assert cpu.registers.flags.subtract == False
    assert cpu.registers.flags.half_carry == False
    assert cpu.registers.flags.carry == False
    print("  PASS")

    # Test 3: DEC SP (0x3B) should leave ALL flags unchanged
    print("\nTest 3: DEC SP with initial F=$F0")
    cpu.memory.write_byte(0x0000, 0x3B)  # DEC SP
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = True
    cpu.registers.flags.subtract = True
    cpu.registers.flags.half_carry = True
    cpu.registers.flags.carry = True
    f_before = get_f_register(cpu.registers.flags)

    cpu.step()
    f_after = get_f_register(cpu.registers.flags)

    print(f"  SP before: 0xDFF0, after: 0x{cpu.registers._sp:04X} (should be 0xDFEF)")
    print(f"  F before: 0x{f_before:02X}, after: 0x{f_after:02X} (should be unchanged)")

    assert cpu.registers._sp == 0xDFEF
    assert f_after == f_before, f"F should be unchanged"
    assert cpu.registers.flags.zero == True
    assert cpu.registers.flags.subtract == True
    assert cpu.registers.flags.half_carry == True
    assert cpu.registers.flags.carry == True
    print("  PASS")

    # Point #2: ADD HL,SP (0x39) should RESET N=0, preserve Z, set H/C
    print("\nTest 4: ADD HL,SP with initial F=$F0 (N should be reset to 0)")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0x1000
    cpu.registers._sp = 0x2000
    # Set all flags including N=1
    cpu.registers.flags.zero = True
    cpu.registers.flags.subtract = True  # N=1 from prior op
    cpu.registers.flags.half_carry = True
    cpu.registers.flags.carry = True

    cpu.step()

    print(f"  HL before: 0x1000, SP: 0x2000")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (should be 0x3000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 1, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0, RESET)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 0)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 0)")

    assert cpu.registers.hl == 0x3000
    assert cpu.registers.flags.zero == True, "Z should be preserved"
    assert cpu.registers.flags.subtract == False, "N should be RESET to 0!"
    assert cpu.registers.flags.half_carry == False
    assert cpu.registers.flags.carry == False
    print("  PASS")

    # Test 5: ADD HL,SP with carry, starting with N=1
    print("\nTest 5: ADD HL,SP with HL=$FFFF, SP=$0001, initial N=1")
    cpu.memory.write_byte(0x0000, 0x39)  # ADD HL,SP
    cpu.registers._pc = 0x0000
    cpu.registers.hl = 0xFFFF
    cpu.registers._sp = 0x0001
    cpu.registers.flags.zero = False
    cpu.registers.flags.subtract = True  # N=1 from prior SUB
    cpu.registers.flags.half_carry = False
    cpu.registers.flags.carry = False

    cpu.step()

    print(f"  HL before: 0xFFFF, SP: 0x0001")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (should be 0x0000)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0, RESET)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers.hl == 0x0000
    assert cpu.registers.flags.zero == False
    assert cpu.registers.flags.subtract == False, "N must be RESET to 0!"
    assert cpu.registers.flags.half_carry == True
    assert cpu.registers.flags.carry == True
    print("  PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("INC/DEC SP leave flags unchanged, ADD HL,SP resets N=0")
    print("=" * 80)

if __name__ == "__main__":
    test_sp_flags()
