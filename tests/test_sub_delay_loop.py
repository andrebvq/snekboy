"""
Test SUB instruction in the exact pattern used in the delay loop
0x0213: SUB 5
0x0215: JR NC, -4
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

def test_sub_delay_loop():
    cpu = CPU()

    print("Testing SUB delay loop pattern")
    print("=" * 80)

    # Setup delay loop code at 0x0213
    cpu.memory.write_byte(0x0213, 0xD6)  # SUB n
    cpu.memory.write_byte(0x0214, 0x05)  # n=5
    cpu.memory.write_byte(0x0215, 0x30)  # JR NC,n
    cpu.memory.write_byte(0x0216, 0xFC)  # n=-4 (jump back to 0x0213)
    cpu.memory.write_byte(0x0217, 0x76)  # HALT (exit)

    cpu.registers._pc = 0x0213
    cpu.registers._a = 0xDF  # Starting value from trace
    cpu.registers._sp = 0xD644

    print(f"Starting: A=0x{cpu.registers._a:02X}")
    print()

    iterations = 0
    max_iterations = 100

    while iterations < max_iterations:
        pc = cpu.registers._pc
        a_before = cpu.registers._a
        f_before = get_f_register(cpu.registers.flags)

        cpu.step()

        a_after = cpu.registers._a
        f_after = get_f_register(cpu.registers.flags)
        pc_after = cpu.registers._pc

        z = int(cpu.registers.flags.zero)
        n = int(cpu.registers.flags.subtract)
        h = int(cpu.registers.flags.half_carry)
        c = int(cpu.registers.flags.carry)

        print(f"[{iterations:>3}] PC=0x{pc:04X} A:0x{a_before:02X}->0x{a_after:02X} F:0x{f_before:02X}->0x{f_after:02X} Z={z} N={n} H={h} C={c} -> PC=0x{pc_after:04X}")

        # Exit when we reach HALT or when carry is set (exit condition)
        if pc_after == 0x0217 or c == 1:
            print(f"\nLoop exited after {iterations + 1} iterations")
            print(f"Final A=0x{cpu.registers._a:02X}, Carry={'SET' if c == 1 else 'CLEAR'}")
            break

        iterations += 1

    if iterations >= max_iterations:
        print(f"\n*** ERROR: Loop did not exit after {max_iterations} iterations! ***")
        print(f"Final A=0x{cpu.registers._a:02X}")
        print(f"Final flags: Z={z} N={n} H={h} C={c}")
        return False

    # Verify we exited correctly (when A-5 would underflow)
    print("\nTest PASSED - delay loop exited correctly")
    return True

def test_specific_sub_values():
    """Test specific SUB values that appeared in the trace"""
    cpu = CPU()

    print("\n" + "=" * 80)
    print("Testing specific SUB operations from trace")
    print("=" * 80)

    test_cases = [
        (0xDF, 0x05, 0xDA, False, False),  # 0xDF - 0x05 = 0xDA, no carry
        (0xDA, 0x05, 0xD5, False, False),
        (0xCB, 0x05, 0xC6, False, False),
        (0x05, 0x05, 0x00, True, False),   # Result is zero
        (0x04, 0x05, 0xFF, False, True),   # Underflow, carry set
        (0x00, 0x05, 0xFB, False, True),   # Underflow from 0
    ]

    for a_val, sub_val, expected_result, expected_z, expected_c in test_cases:
        cpu.memory.write_byte(0x0000, 0xD6)  # SUB n
        cpu.memory.write_byte(0x0001, sub_val)
        cpu.registers._pc = 0x0000
        cpu.registers._a = a_val

        cpu.step()

        result = cpu.registers._a
        z = cpu.registers.flags.zero
        c = cpu.registers.flags.carry
        n = cpu.registers.flags.subtract
        h = cpu.registers.flags.half_carry

        print(f"  0x{a_val:02X} - 0x{sub_val:02X} = 0x{result:02X} (expected 0x{expected_result:02X}) Z={int(z)} N={int(n)} H={int(h)} C={int(c)}", end="")

        if result == expected_result and z == expected_z and c == expected_c and n == True:
            print(" PASS")
        else:
            print(f" FAIL")
            if result != expected_result:
                print(f"    Result mismatch: got 0x{result:02X}, expected 0x{expected_result:02X}")
            if z != expected_z:
                print(f"    Z flag mismatch: got {z}, expected {expected_z}")
            if c != expected_c:
                print(f"    C flag mismatch: got {c}, expected {expected_c}")
            if n != True:
                print(f"    N flag should always be True for SUB, got {n}")
            return False

    print("\nAll specific SUB tests PASSED")
    return True

if __name__ == "__main__":
    success1 = test_sub_delay_loop()
    success2 = test_specific_sub_values()

    if success1 and success2:
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)
