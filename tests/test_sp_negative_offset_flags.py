"""
Test half-carry and carry flags for ADD SP,e and LD HL,SP+e with negative offsets
This checks point #1 from the analysis
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

def test_negative_offsets():
    cpu = CPU()

    print("Testing H/C flags for ADD SP,e and LD HL,SP+e with negative offsets")
    print("=" * 80)

    # Test case from source: SP=$00FF, e=$FF (-1)
    # Low byte calculation: $FF + $FF = $1FE
    # H should be 1 (carry from bit 3: $F + $F = $1E, bit 3 overflow)
    # C should be 1 (carry from bit 7: $FF + $FF = $1FE > $FF)
    print("\nTest 1: ADD SP,$FF with SP=$00FF")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0xFF)  # e=-1
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x00FF
    cpu.registers.flags.zero = False
    cpu.step()

    print(f"  SP before: 0x00FF")
    print(f"  SP after:  0x{cpu.registers._sp:04X} (expected 0x00FE)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers._sp == 0x00FE, f"SP should be 0x00FE, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == False, "Z should be preserved (0)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == True, "H should be 1 (carry from bit 3)"
    assert cpu.registers.flags.carry == True, "C should be 1 (carry from bit 7)"
    print("  PASS: PASS")

    # Test case: SP=$0000, e=$FF (-1)
    # Low byte calculation: $00 + $FF = $FF
    # H should be 0 (no carry from bit 3: $0 + $F = $F, no overflow)
    # C should be 0 (no carry from bit 7: $00 + $FF = $FF, no overflow)
    print("\nTest 2: ADD SP,$FF with SP=$0000")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0xFF)  # e=-1
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x0000
    cpu.registers.flags.zero = True
    cpu.step()

    print(f"  SP before: 0x0000")
    print(f"  SP after:  0x{cpu.registers._sp:04X} (expected 0xFFFF)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 1, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 0)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 0)")

    assert cpu.registers._sp == 0xFFFF, f"SP should be 0xFFFF, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == True, "Z should be preserved (1)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == False, "H should be 0"
    assert cpu.registers.flags.carry == False, "C should be 0"
    print("  PASS: PASS")

    # Test case: LD HL,SP+$FF with SP=$00FF
    print("\nTest 3: LD HL,SP+$FF with SP=$00FF")
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
    cpu.memory.write_byte(0x0001, 0xFF)  # e=-1
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x00FF
    cpu.registers.flags.zero = False
    cpu.step()

    print(f"  SP: 0x00FF (unchanged)")
    print(f"  HL after: 0x{cpu.registers.hl:04X} (expected 0x00FE)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers.hl == 0x00FE, f"HL should be 0x00FE, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == False, "Z should be preserved (0)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == True, "H should be 1"
    assert cpu.registers.flags.carry == True, "C should be 1"
    print("  PASS: PASS")

    # Boundary case: SP=$FFFF, e=$FF
    print("\nTest 4: ADD SP,$FF with SP=$FFFF")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0xFF)  # e=-1
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xFFFF
    cpu.registers.flags.zero = True
    cpu.step()

    print(f"  SP before: 0xFFFF")
    print(f"  SP after:  0x{cpu.registers._sp:04X} (expected 0xFFFE)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 1, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 1)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 1)")

    assert cpu.registers._sp == 0xFFFE, f"SP should be 0xFFFE, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == True, "Z should be preserved (1)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == True, "H should be 1 ($F + $F overflow)"
    assert cpu.registers.flags.carry == True, "C should be 1 ($FF + $FF overflow)"
    print("  PASS: PASS")

    # Test case: SP=$0010, e=$01 (positive for comparison)
    print("\nTest 5: ADD SP,$01 with SP=$0010 (positive offset)")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0x01)  # e=+1
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x0010
    cpu.registers.flags.zero = False
    cpu.step()

    print(f"  SP before: 0x0010")
    print(f"  SP after:  0x{cpu.registers._sp:04X} (expected 0x0011)")
    print(f"  Z: {int(cpu.registers.flags.zero)} (should be 0, preserved)")
    print(f"  N: {int(cpu.registers.flags.subtract)} (should be 0)")
    print(f"  H: {int(cpu.registers.flags.half_carry)} (should be 0)")
    print(f"  C: {int(cpu.registers.flags.carry)} (should be 0)")

    assert cpu.registers._sp == 0x0011, f"SP should be 0x0011, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == False, "Z should be preserved (0)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == False, "H should be 0"
    assert cpu.registers.flags.carry == False, "C should be 0"
    print("  PASS: PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("H/C flags correctly calculated for negative offsets")
    print("=" * 80)

if __name__ == "__main__":
    test_negative_offsets()
