"""
Test INC SP in full loop pattern mimicking Blargg source
This addresses recommendation #2 - INC SP with F=$F0 in complete loop
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

def test_inc_sp_loop():
    print("Testing INC SP in full loop pattern with F=$F0")
    print("=" * 80)

    # Test critical SP values from Blargg source
    sp_values = [
        0x0000,  # Zero
        0x0001,  # Just after zero
        0x00FF,  # Low byte boundary
        0x0FFF,  # Mid boundary
        0x7FFF,  # Sign bit boundary
        0x8000,  # High bit set
        0xFFFF,  # Wrap boundary
    ]

    for sp_val in sp_values:
        cpu = CPU()

        sp_expected = (sp_val + 1) & 0xFFFF

        print(f"\nTest: SP=0x{sp_val:04X} -> 0x{sp_expected:04X}")
        print("-" * 60)

        addr = 0xC100

        # Set F=$F0 via PUSH BC / POP AF
        cpu.memory.write_byte(addr + 0, 0x01)   # LD BC,$AAF0
        cpu.memory.write_byte(addr + 1, 0xF0)
        cpu.memory.write_byte(addr + 2, 0xAA)
        cpu.memory.write_byte(addr + 3, 0xC5)   # PUSH BC
        cpu.memory.write_byte(addr + 4, 0xF1)   # POP AF

        # Set SP
        cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,nn
        cpu.memory.write_byte(addr + 6, sp_val & 0xFF)
        cpu.memory.write_byte(addr + 7, (sp_val >> 8) & 0xFF)

        # Save original SP to temp ($C000)
        cpu.memory.write_byte(addr + 8, 0x08)   # LD ($C000),SP
        cpu.memory.write_byte(addr + 9, 0x00)
        cpu.memory.write_byte(addr + 10, 0xC0)

        # INC SP
        cpu.memory.write_byte(addr + 11, 0x33)

        # Save new SP to temp+2 ($C002)
        cpu.memory.write_byte(addr + 12, 0x08)  # LD ($C002),SP
        cpu.memory.write_byte(addr + 13, 0x02)
        cpu.memory.write_byte(addr + 14, 0xC0)

        # HALT
        cpu.memory.write_byte(addr + 15, 0x76)

        cpu.registers._pc = addr
        cpu.registers._sp = 0xDFF0

        # Execute
        for i in range(10):
            cpu.step()

        # Check results
        a = cpu.registers._a
        f = get_f_register(cpu.registers.flags)
        sp_final = cpu.registers._sp

        sp_orig_low = cpu.memory.read_byte(0xC000)
        sp_orig_high = cpu.memory.read_byte(0xC001)
        sp_new_low = cpu.memory.read_byte(0xC002)
        sp_new_high = cpu.memory.read_byte(0xC003)

        # Reconstruct
        sp_orig = sp_orig_low | (sp_orig_high << 8)
        sp_new = sp_new_low | (sp_new_high << 8)

        # Calculate "checksum" (AF + temp+2 bytes)
        checksum = a ^ f ^ sp_new_low ^ sp_new_high

        print(f"  A=0x{a:02X} F=0x{f:02X} SP=0x{sp_final:04X}")
        print(f"  Original SP: 0x{sp_orig:04X}")
        print(f"  New SP:      0x{sp_new:04X} (expected 0x{sp_expected:04X})")
        print(f"  Checksum:    0x{checksum:02X}")

        # Critical checks
        if f != 0xF0:
            print(f"  *** FAIL: F changed from 0xF0 to 0x{f:02X} ***")
            print(f"      Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
            print(f"  >>> BUG: INC SP is modifying flags! <<<")
            return False

        if sp_final != sp_expected:
            print(f"  *** FAIL: SP incorrect ***")
            return False

        if sp_orig != sp_val:
            print(f"  *** FAIL: Original SP not saved correctly ***")
            return False

        if sp_new != sp_expected:
            print(f"  *** FAIL: New SP not saved correctly ***")
            print(f"      Bytes: low=0x{sp_new_low:02X}, high=0x{sp_new_high:02X}")
            return False

        print("  PASS")

    # Special test: Verify handler doesn't touch flags at all
    print(f"\n--- Special verification: INC SP handler flag isolation ---")

    # Test with each flag bit individually
    flag_tests = [
        (0x00, "all clear"),
        (0x10, "C only"),
        (0x20, "H only"),
        (0x40, "N only"),
        (0x80, "Z only"),
        (0xF0, "all set"),
    ]

    for f_val, desc in flag_tests:
        cpu = CPU()  # Fresh CPU for each flag test
        cpu.memory.write_byte(0x0100, 0x01)  # LD BC,nn
        cpu.memory.write_byte(0x0101, f_val)
        cpu.memory.write_byte(0x0102, 0xAA)
        cpu.memory.write_byte(0x0103, 0xC5)  # PUSH BC
        cpu.memory.write_byte(0x0104, 0xF1)  # POP AF
        cpu.memory.write_byte(0x0105, 0x31)  # LD SP,$FFFF
        cpu.memory.write_byte(0x0106, 0xFF)
        cpu.memory.write_byte(0x0107, 0xFF)
        cpu.memory.write_byte(0x0108, 0x33)  # INC SP
        cpu.memory.write_byte(0x0109, 0x76)  # HALT

        cpu.registers._pc = 0x0100
        cpu.registers._sp = 0xDFF0

        for _ in range(6):
            cpu.step()

        f_after = get_f_register(cpu.registers.flags)
        if f_after != f_val:
            print(f"  FAIL: {desc} - F changed from 0x{f_val:02X} to 0x{f_after:02X}")
            return False

    print("  PASS: All flag patterns preserved")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("INC SP correctly preserves F bit-for-bit in all contexts")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_inc_sp_loop()
    if not success:
        sys.exit(1)
