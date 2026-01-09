"""
Test INC SP with ALL flag combinations and boundary SP values
This is hypothesis #2 - flags not completely unchanged
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

def set_f_register(cpu, f_value):
    """Set F register from byte value"""
    cpu.registers.flags.zero = (f_value & 0x80) != 0
    cpu.registers.flags.subtract = (f_value & 0x40) != 0
    cpu.registers.flags.half_carry = (f_value & 0x20) != 0
    cpu.registers.flags.carry = (f_value & 0x10) != 0

def test_inc_sp_flags():
    cpu = CPU()

    print("Testing INC SP preserves ALL flags for all combinations")
    print("=" * 80)

    # Test all 16 possible flag combinations (Z, N, H, C can each be 0 or 1)
    flag_values = [
        0x00,  # All clear
        0x10,  # C only
        0x20,  # H only
        0x30,  # H+C
        0x40,  # N only
        0x50,  # N+C
        0x60,  # N+H
        0x70,  # N+H+C
        0x80,  # Z only
        0x90,  # Z+C
        0xA0,  # Z+H
        0xB0,  # Z+H+C
        0xC0,  # Z+N
        0xD0,  # Z+N+C
        0xE0,  # Z+N+H
        0xF0,  # All set
    ]

    # Test with critical SP values
    sp_values = [
        0x0000,  # Boundary
        0x0001,
        0x00FF,  # Low byte boundary
        0x0FFF,  # Half-carry boundary in high byte
        0x7FFF,  # Sign boundary
        0xFFFF,  # Wrap boundary
    ]

    failures = []

    for sp_val in sp_values:
        for f_val in flag_values:
            # Setup INC SP
            cpu.memory.write_byte(0x0000, 0x33)  # INC SP
            cpu.registers._pc = 0x0000
            cpu.registers._sp = sp_val
            set_f_register(cpu, f_val)

            f_before = get_f_register(cpu.registers.flags)

            # Execute INC SP
            cpu.step()

            f_after = get_f_register(cpu.registers.flags)
            sp_after = cpu.registers._sp
            sp_expected = (sp_val + 1) & 0xFFFF

            # Check SP value
            if sp_after != sp_expected:
                msg = f"SP mismatch: SP=0x{sp_val:04X}, F=0x{f_val:02X} -> SP=0x{sp_after:04X} (expected 0x{sp_expected:04X})"
                print(f"  FAIL: {msg}")
                failures.append(msg)

            # Check flags unchanged
            if f_after != f_before:
                msg = f"Flag changed: SP=0x{sp_val:04X}, F=0x{f_before:02X} -> F=0x{f_after:02X} (should be unchanged)"
                print(f"  FAIL: {msg}")
                z_b = int(cpu.registers.flags.zero)
                n_b = int(cpu.registers.flags.subtract)
                h_b = int(cpu.registers.flags.half_carry)
                c_b = int(cpu.registers.flags.carry)
                print(f"         Flags after: Z={z_b} N={n_b} H={h_b} C={c_b}")
                failures.append(msg)

    if failures:
        print()
        print("=" * 80)
        print(f"FAILED: {len(failures)} test(s) failed")
        for failure in failures[:10]:  # Show first 10
            print(f"  - {failure}")
        if len(failures) > 10:
            print(f"  ... and {len(failures) - 10} more")
        print("=" * 80)
        return False
    else:
        print()
        print(f"Tested {len(sp_values) * len(flag_values)} combinations")
        print("=" * 80)
        print("ALL TESTS PASSED!")
        print("INC SP correctly preserves ALL flags for all SP values")
        print("=" * 80)
        return True

if __name__ == "__main__":
    success = test_inc_sp_flags()
    if not success:
        sys.exit(1)
