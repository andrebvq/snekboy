"""
Unit test for SP/HL instruction flag behavior
Based on Game Boy CPU manual specifications
"""

from src.cpu import CPU

def test_add_sp_n_flags():
    """Test ADD SP,n flag setting"""
    print("Testing ADD SP,n flag behavior...")
    print("=" * 70)

    tests = [
        # (SP_before, offset, expected_H, expected_C, description)
        (0xFFF8, 0x08, True, True, "SP=0xFFF8 + 8: H=1 (0xF8+0x08>0xFF), C=1 (0xF8+0x08>0xFF)"),
        (0xFFF8, 0xF8, True, True, "SP=0xFFF8 + (-8): H=1, C=1"),  # 0xF8 as signed = -8
        (0x0000, 0x00, False, False, "SP=0x0000 + 0: H=0, C=0"),
        (0x000F, 0x01, True, False, "SP=0x000F + 1: H=1 (0x0F+0x01>0x0F), C=0"),
        (0x00FF, 0x01, True, True, "SP=0x00FF + 1: H=1, C=1 (0xFF+0x01>0xFF)"),
    ]

    for sp_val, offset, exp_h, exp_c, desc in tests:
        cpu = CPU()
        # Set up SP
        cpu.registers._sp = sp_val

        # Manually write ADD SP,n instruction at 0x0100 (where PC starts)
        cpu.memory._data[0x0100] = 0xE8  # ADD SP,n
        cpu.memory._data[0x0101] = offset

        # Execute
        cpu.step()

        # Check flags
        actual_h = cpu.registers.flags.half_carry
        actual_c = cpu.registers.flags.carry
        z = cpu.registers.flags.zero
        n = cpu.registers.flags.subtract

        # Calculate expected SP
        signed_offset = offset if offset < 128 else offset - 256
        expected_sp = (sp_val + signed_offset) & 0xFFFF

        passed = (actual_h == exp_h and actual_c == exp_c and z == False and n == False)
        status = "[PASS]" if passed else "[FAIL]"

        print(f"\n{status}: {desc}")
        print(f"  SP: 0x{sp_val:04X} + {signed_offset:+d} = 0x{cpu.registers._sp:04X} (expected 0x{expected_sp:04X})")
        print(f"  Flags: Z={z} N={n} H={actual_h} C={actual_c}")
        if not passed:
            print(f"  Expected: Z=False N=False H={exp_h} C={exp_c}")

    print("\n" + "=" * 70)

def test_ld_hl_sp_n_flags():
    """Test LD HL,SP+n flag setting"""
    print("\nTesting LD HL,SP+n flag behavior...")
    print("=" * 70)

    tests = [
        # (SP_before, offset, expected_H, expected_C, description)
        (0xFFF8, 0x08, True, True, "SP=0xFFF8 + 8"),
        (0xFFF8, 0xF8, True, True, "SP=0xFFF8 + (-8)"),
        (0x0000, 0x00, False, False, "SP=0x0000 + 0"),
        (0x000F, 0x01, True, False, "SP=0x000F + 1"),
        (0x00FF, 0x01, True, True, "SP=0x00FF + 1"),
    ]

    for sp_val, offset, exp_h, exp_c, desc in tests:
        cpu = CPU()
        cpu.registers._sp = sp_val

        # Write LD HL,SP+n instruction at 0x0100 (where PC starts)
        cpu.memory._data[0x0100] = 0xF8  # LD HL,SP+n
        cpu.memory._data[0x0101] = offset

        cpu.step()

        actual_h = cpu.registers.flags.half_carry
        actual_c = cpu.registers.flags.carry
        z = cpu.registers.flags.zero
        n = cpu.registers.flags.subtract

        signed_offset = offset if offset < 128 else offset - 256
        expected_hl = (sp_val + signed_offset) & 0xFFFF

        passed = (actual_h == exp_h and actual_c == exp_c and z == False and n == False)
        status = "[PASS]" if passed else "[FAIL]"

        print(f"\n{status}: {desc}")
        print(f"  SP=0x{sp_val:04X} + {signed_offset:+d} -> HL=0x{cpu.registers.hl:04X} (expected 0x{expected_hl:04X})")
        print(f"  Flags: Z={z} N={n} H={actual_h} C={actual_c}")
        if not passed:
            print(f"  Expected: Z=False N=False H={exp_h} C={exp_c}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_add_sp_n_flags()
    test_ld_hl_sp_n_flags()
