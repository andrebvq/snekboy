"""
Test POP AF to verify flag register behavior
"""

from src.cpu import CPU

def test_pop_af_flag_masking():
    """Test that POP AF masks lower 4 bits of F register"""
    cpu = CPU()

    # Push a value with lower 4 bits set (should be masked on POP)
    # Set AF = 0x12FF (A=0x12, F=0xFF with all bits set)
    cpu.registers._sp = 0xFFFE

    # Manually write to stack: low byte (F), then high byte (A)
    cpu.memory.write_byte(0xFFFC, 0xFF)  # F register with all bits set
    cpu.memory.write_byte(0xFFFD, 0x12)  # A register
    cpu.registers._sp = 0xFFFC

    print(f"Before POP AF:")
    print(f"  SP = 0x{cpu.registers._sp:04X}")
    print(f"  Stack[SP] = 0x{cpu.memory.read_byte(0xFFFC):02X} (will become F)")
    print(f"  Stack[SP+1] = 0x{cpu.memory.read_byte(0xFFFD):02X} (will become A)")

    # Execute POP AF
    cpu._execute_pop('AF')

    print(f"\nAfter POP AF:")
    print(f"  A = 0x{cpu.registers._a:02X} (expected: 0x12)")
    print(f"  F = 0x{cpu.registers._flags.to_byte():02X} (expected: 0xF0, got with lower 4 bits)")
    print(f"  AF = 0x{cpu.registers.af:04X}")
    print(f"  SP = 0x{cpu.registers._sp:04X} (expected: 0xFFFE)")

    f_value = cpu.registers._flags.to_byte()

    # On Game Boy, F register should have lower 4 bits always 0
    if f_value == 0xF0:
        print("\n[PASS] F register correctly masked to 0xF0")
        return True
    elif f_value == 0xFF:
        print(f"\n[FAIL] F register NOT masked! Got 0xFF instead of 0xF0")
        print("  This is the bug! Lower 4 bits should always be 0")
        return False
    else:
        print(f"\n[FAIL] Unexpected F value: 0x{f_value:02X}")
        return False

def test_pop_af_individual_flags():
    """Test that individual flags are correctly restored"""
    cpu = CPU()

    # Test with specific flag pattern: Z=1, N=0, H=1, C=0 = 0xA0
    cpu.registers._sp = 0xFFFC
    cpu.memory.write_byte(0xFFFC, 0xA0)  # Z and H set
    cpu.memory.write_byte(0xFFFD, 0x34)  # A = 0x34

    print("\n" + "="*50)
    print("Test 2: Individual flag restoration")
    print("="*50)

    cpu._execute_pop('AF')

    print(f"A = 0x{cpu.registers._a:02X} (expected: 0x34)")
    print(f"F = 0x{cpu.registers._flags.to_byte():02X} (expected: 0xA0)")
    print(f"Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")
    print(f"Expected: Z=1, N=0, H=1, C=0")

    if (cpu.registers._a == 0x34 and
        cpu.registers.flags.zero == True and
        cpu.registers.flags.subtract == False and
        cpu.registers.flags.half_carry == True and
        cpu.registers.flags.carry == False):
        print("[PASS] Flags correctly restored")
        return True
    else:
        print("[FAIL] Flags not correctly restored")
        return False

def test_push_pop_roundtrip():
    """Test that PUSH AF then POP AF preserves values correctly"""
    cpu = CPU()

    print("\n" + "="*50)
    print("Test 3: PUSH/POP roundtrip")
    print("="*50)

    # Set AF to known value
    cpu.registers._a = 0x42
    cpu.registers.flags.zero = True
    cpu.registers.flags.subtract = False
    cpu.registers.flags.half_carry = True
    cpu.registers.flags.carry = True

    original_af = cpu.registers.af
    original_f = cpu.registers._flags.to_byte()

    print(f"Original: AF=0x{original_af:04X}, F=0x{original_f:02X}")
    print(f"  Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")

    # PUSH AF
    cpu._execute_push('AF')

    # Corrupt AF
    cpu.registers._a = 0x00
    cpu.registers.flags.zero = False
    cpu.registers.flags.subtract = True
    cpu.registers.flags.half_carry = False
    cpu.registers.flags.carry = False

    print(f"After corruption: AF=0x{cpu.registers.af:04X}")

    # POP AF
    cpu._execute_pop('AF')

    restored_af = cpu.registers.af
    restored_f = cpu.registers._flags.to_byte()

    print(f"Restored: AF=0x{restored_af:04X}, F=0x{restored_f:02X}")
    print(f"  Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")

    # F register should be masked to 0xF0 (upper nibble only)
    # Original was 0xD0 (Z=1, N=0, H=1, C=1 with lower bits 0)
    expected_f = original_f & 0xF0

    if restored_af == original_af:
        print(f"[PASS] AF correctly restored")
        return True
    else:
        print(f"[FAIL] AF not correctly restored: expected 0x{original_af:04X}, got 0x{restored_af:04X}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("POP AF FLAG REGISTER TESTS")
    print("="*60)

    results = []
    results.append(("Flag masking", test_pop_af_flag_masking()))
    results.append(("Individual flags", test_pop_af_individual_flags()))
    results.append(("PUSH/POP roundtrip", test_push_pop_roundtrip()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} passed")
