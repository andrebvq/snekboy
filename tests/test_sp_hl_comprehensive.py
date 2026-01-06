"""
Comprehensive standalone tests for all SP/HL instructions
Tests each instruction thoroughly with various values and edge cases
"""

from src.cpu import CPU

def create_cpu_at_0x100():
    """Helper to create CPU with PC at 0x0100 where execution starts"""
    cpu = CPU()
    # PC starts at 0x0100 on Game Boy
    return cpu

def test_add_hl_sp():
    """Test ADD HL,SP (opcode 0x39)"""
    print("\n" + "="*70)
    print("Testing ADD HL,SP (0x39)")
    print("="*70)

    test_cases = [
        # (HL_before, SP, expected_HL, expected_H, expected_C, description)
        (0x0000, 0x0000, 0x0000, False, False, "0x0000 + 0x0000"),
        (0x1234, 0x5678, 0x68AC, False, False, "0x1234 + 0x5678"),
        (0x0FFF, 0x0001, 0x1000, True, False, "Half-carry from bit 11"),
        (0xFFFF, 0x0001, 0x0000, True, True, "Carry from overflow"),
        (0x8000, 0x8000, 0x0000, False, True, "Carry without half-carry"),
        (0x0800, 0x0800, 0x1000, True, False, "Half-carry at bit 11"),
        (0xF000, 0x2000, 0x1000, False, True, "Overflow: (0xF000&0xFFF)+(0x2000&0xFFF)=0x1000, no H"),
    ]

    passed = 0
    failed = 0

    for hl_val, sp_val, exp_hl, exp_h, exp_c, desc in test_cases:
        cpu = create_cpu_at_0x100()
        cpu.registers.hl = hl_val
        cpu.registers._sp = sp_val

        # Write ADD HL,SP at 0x0100
        cpu.memory._data[0x0100] = 0x39

        # Save Z and N flags - they should not be affected
        cpu.registers.flags.zero = True
        cpu.registers.flags.subtract = True

        cpu.step()

        # Check result
        actual_hl = cpu.registers.hl
        actual_h = cpu.registers.flags.half_carry
        actual_c = cpu.registers.flags.carry
        z_preserved = cpu.registers.flags.zero
        n_reset = not cpu.registers.flags.subtract

        success = (
            actual_hl == exp_hl and
            actual_h == exp_h and
            actual_c == exp_c and
            z_preserved and  # Z should be preserved
            n_reset  # N should be reset
        )

        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {desc}")
        print(f"  HL: 0x{hl_val:04X} + SP: 0x{sp_val:04X} = 0x{actual_hl:04X} (expected 0x{exp_hl:04X})")
        print(f"  Flags: H={actual_h} C={actual_c} (expected H={exp_h} C={exp_c})")

        if not success:
            print(f"  ERROR: Expected HL=0x{exp_hl:04X} H={exp_h} C={exp_c}")
            print(f"         Got      HL=0x{actual_hl:04X} H={actual_h} C={actual_c}")
            failed += 1
        else:
            passed += 1

    print(f"\nADD HL,SP: {passed} passed, {failed} failed")
    return failed == 0

def test_ld_sp_hl():
    """Test LD SP,HL (opcode 0xF9)"""
    print("\n" + "="*70)
    print("Testing LD SP,HL (0xF9)")
    print("="*70)

    test_cases = [
        (0x0000, "Zero"),
        (0xFFFF, "Max value"),
        (0x1234, "Random value 1"),
        (0xABCD, "Random value 2"),
        (0xDFFF, "Typical stack pointer"),
    ]

    passed = 0
    failed = 0

    for hl_val, desc in test_cases:
        cpu = create_cpu_at_0x100()
        cpu.registers.hl = hl_val
        cpu.registers._sp = 0x0000  # Set SP to different value

        # Write LD SP,HL at 0x0100
        cpu.memory._data[0x0100] = 0xF9

        cpu.step()

        # Check result
        actual_sp = cpu.registers._sp
        success = actual_sp == hl_val

        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {desc}: HL=0x{hl_val:04X} -> SP=0x{actual_sp:04X}")

        if not success:
            print(f"  ERROR: Expected SP=0x{hl_val:04X}, got SP=0x{actual_sp:04X}")
            failed += 1
        else:
            passed += 1

    print(f"\nLD SP,HL: {passed} passed, {failed} failed")
    return failed == 0

def test_add_sp_n():
    """Test ADD SP,n (opcode 0xE8)"""
    print("\n" + "="*70)
    print("Testing ADD SP,n (0xE8)")
    print("="*70)

    test_cases = [
        # (SP_before, offset, expected_SP, expected_H, expected_C, description)
        (0x0000, 0x00, 0x0000, False, False, "SP + 0"),
        (0x000F, 0x01, 0x0010, True, False, "Half-carry at bit 3"),
        (0x00FF, 0x01, 0x0100, True, True, "Carry at bit 7"),
        (0xFFF8, 0x08, 0x0000, True, True, "Both flags, wraparound"),
        (0x1234, 0x10, 0x1244, False, False, "Positive offset, no flags"),
        (0x1234, 0xF0, 0x1224, False, True, "Negative offset (-16): C=1 from 0x34+0xF0"),
        (0x0010, 0xFF, 0x000F, False, True, "Negative offset (-1): 0x10+0xFF, H=0 C=1"),
        (0x0000, 0xFF, 0xFFFF, False, False, "0 + (-1): 0x00+0xFF, no flags"),
        (0xFFFF, 0x01, 0x0000, True, True, "Wraparound with positive"),
    ]

    passed = 0
    failed = 0

    for sp_val, offset, exp_sp, exp_h, exp_c, desc in test_cases:
        cpu = create_cpu_at_0x100()
        cpu.registers._sp = sp_val

        # Write ADD SP,n at 0x0100
        cpu.memory._data[0x0100] = 0xE8
        cpu.memory._data[0x0101] = offset

        cpu.step()

        # Check result
        actual_sp = cpu.registers._sp
        actual_h = cpu.registers.flags.half_carry
        actual_c = cpu.registers.flags.carry
        z_reset = not cpu.registers.flags.zero
        n_reset = not cpu.registers.flags.subtract

        success = (
            actual_sp == exp_sp and
            actual_h == exp_h and
            actual_c == exp_c and
            z_reset and  # Z always reset
            n_reset  # N always reset
        )

        signed_offset = offset if offset < 128 else offset - 256
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {desc}")
        print(f"  SP: 0x{sp_val:04X} + {signed_offset:+d} = 0x{actual_sp:04X} (expected 0x{exp_sp:04X})")
        print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={actual_h} C={actual_c}")

        if not success:
            print(f"  ERROR: Expected SP=0x{exp_sp:04X} H={exp_h} C={exp_c}")
            print(f"         Got      SP=0x{actual_sp:04X} H={actual_h} C={actual_c}")
            failed += 1
        else:
            passed += 1

    print(f"\nADD SP,n: {passed} passed, {failed} failed")
    return failed == 0

def test_ld_hl_sp_n():
    """Test LD HL,SP+n (opcode 0xF8)"""
    print("\n" + "="*70)
    print("Testing LD HL,SP+n (0xF8)")
    print("="*70)

    test_cases = [
        # (SP, offset, expected_HL, expected_H, expected_C, description)
        (0x0000, 0x00, 0x0000, False, False, "SP + 0"),
        (0x000F, 0x01, 0x0010, True, False, "Half-carry at bit 3"),
        (0x00FF, 0x01, 0x0100, True, True, "Carry at bit 7"),
        (0xFFF8, 0x08, 0x0000, True, True, "Both flags, wraparound"),
        (0x1234, 0x10, 0x1244, False, False, "Positive offset"),
        (0x1234, 0xF0, 0x1224, False, True, "Negative offset (-16): C=1 from 0x34+0xF0"),
        (0x0010, 0xFF, 0x000F, False, True, "Negative offset (-1): 0x10+0xFF, H=0 C=1"),
        (0xD65C, 0x00, 0xD65C, False, False, "Actual value from test 03"),
        (0x0000, 0xFF, 0xFFFF, False, False, "0 + (-1): 0x00+0xFF, no flags"),
    ]

    passed = 0
    failed = 0

    for sp_val, offset, exp_hl, exp_h, exp_c, desc in test_cases:
        cpu = create_cpu_at_0x100()
        cpu.registers._sp = sp_val
        cpu.registers.hl = 0x0000  # Set HL to different value

        # Write LD HL,SP+n at 0x0100
        cpu.memory._data[0x0100] = 0xF8
        cpu.memory._data[0x0101] = offset

        cpu.step()

        # Check result
        actual_hl = cpu.registers.hl
        actual_sp = cpu.registers._sp  # SP should not change
        actual_h = cpu.registers.flags.half_carry
        actual_c = cpu.registers.flags.carry
        z_reset = not cpu.registers.flags.zero
        n_reset = not cpu.registers.flags.subtract

        success = (
            actual_hl == exp_hl and
            actual_sp == sp_val and  # SP unchanged
            actual_h == exp_h and
            actual_c == exp_c and
            z_reset and  # Z always reset
            n_reset  # N always reset
        )

        signed_offset = offset if offset < 128 else offset - 256
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {desc}")
        print(f"  SP: 0x{sp_val:04X} + {signed_offset:+d} -> HL=0x{actual_hl:04X} (expected 0x{exp_hl:04X})")
        print(f"  SP unchanged: 0x{actual_sp:04X} (expected 0x{sp_val:04X})")
        print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={actual_h} C={actual_c}")

        if not success:
            print(f"  ERROR: Expected HL=0x{exp_hl:04X} SP=0x{sp_val:04X} H={exp_h} C={exp_c}")
            print(f"         Got      HL=0x{actual_hl:04X} SP=0x{actual_sp:04X} H={actual_h} C={actual_c}")
            failed += 1
        else:
            passed += 1

    print(f"\nLD HL,SP+n: {passed} passed, {failed} failed")
    return failed == 0

def test_edge_cases():
    """Test edge cases and flag interactions"""
    print("\n" + "="*70)
    print("Testing Edge Cases and Flag Interactions")
    print("="*70)

    # Test that ADD HL,SP preserves Z flag
    print("\n[Test 1] ADD HL,SP should preserve Z flag")
    cpu = create_cpu_at_0x100()
    cpu.registers.hl = 0x1000
    cpu.registers._sp = 0x2000
    cpu.registers.flags.zero = True
    cpu.memory._data[0x0100] = 0x39  # ADD HL,SP
    cpu.step()

    if cpu.registers.flags.zero:
        print("  [PASS] Z flag preserved")
    else:
        print("  [FAIL] Z flag should be preserved but was reset")
        return False

    # Test that ADD HL,SP resets N flag
    print("\n[Test 2] ADD HL,SP should reset N flag")
    cpu = create_cpu_at_0x100()
    cpu.registers.hl = 0x1000
    cpu.registers._sp = 0x2000
    cpu.registers.flags.subtract = True
    cpu.memory._data[0x0100] = 0x39  # ADD HL,SP
    cpu.step()

    if not cpu.registers.flags.subtract:
        print("  [PASS] N flag reset")
    else:
        print("  [FAIL] N flag should be reset")
        return False

    # Test ADD SP,n with boundary values
    print("\n[Test 3] ADD SP,n at boundaries")
    test_vals = [
        (0x00F0, 0x0F, 0x00FF, False, False),  # 0xF0+0x0F=0xFF: no carries
        (0x00F0, 0x10, 0x0100, False, True),   # 0xF0+0x10=0x100: C from bit7
    ]

    for sp, offset, exp_sp, exp_h, exp_c in test_vals:
        cpu = create_cpu_at_0x100()
        cpu.registers._sp = sp
        cpu.memory._data[0x0100] = 0xE8
        cpu.memory._data[0x0101] = offset
        cpu.step()

        if cpu.registers._sp == exp_sp and cpu.registers.flags.half_carry == exp_h and cpu.registers.flags.carry == exp_c:
            print(f"  [PASS] SP=0x{sp:04X} + 0x{offset:02X} = 0x{cpu.registers._sp:04X}")
        else:
            print(f"  [FAIL] SP=0x{sp:04X} + 0x{offset:02X} got 0x{cpu.registers._sp:04X}, expected 0x{exp_sp:04X}")
            return False

    print("\n[PASS] All edge cases passed")
    return True

def main():
    print("="*70)
    print("COMPREHENSIVE SP/HL INSTRUCTION TESTS")
    print("="*70)

    results = {
        "ADD HL,SP": test_add_hl_sp(),
        "LD SP,HL": test_ld_sp_hl(),
        "ADD SP,n": test_add_sp_n(),
        "LD HL,SP+n": test_ld_hl_sp_n(),
        "Edge Cases": test_edge_cases(),
    }

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    print("="*70)
    if all_passed:
        print("ALL TESTS PASSED!")
        print("SP/HL instructions are working correctly.")
    else:
        print("SOME TESTS FAILED!")
        print("There are bugs in the SP/HL instruction implementations.")
    print("="*70)

    return all_passed

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
