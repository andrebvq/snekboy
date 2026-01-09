"""
Test PUSH BC / POP AF specifically with C flag only (0x10)
This reproduces the bug found in the full loop test
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

def test_push_pop_c_only():
    cpu = CPU()

    print("Testing PUSH BC / POP AF with C flag only (BC=$AA10)")
    print("=" * 80)

    # Set BC to $AA10
    cpu.memory.write_byte(0x0100, 0x01)  # LD BC,$10AA
    cpu.memory.write_byte(0x0101, 0x10)  # Low byte = $10 (will become F)
    cpu.memory.write_byte(0x0102, 0xAA)  # High byte = $AA (will become A)
    cpu.memory.write_byte(0x0103, 0xC5)  # PUSH BC
    cpu.memory.write_byte(0x0104, 0xF1)  # POP AF
    cpu.memory.write_byte(0x0105, 0x76)  # HALT

    cpu.registers._pc = 0x0100
    cpu.registers._sp = 0xDFF0
    cpu.registers._b = 0xFF
    cpu.registers._c = 0xFF

    print(f"Before PUSH:")
    print(f"  BC=0x{cpu.registers.bc:04X}")
    print(f"  SP=0x{cpu.registers._sp:04X}")

    # Execute LD BC,$10AA
    cpu.step()
    print(f"\nAfter LD BC,$10AA:")
    print(f"  BC=0x{cpu.registers.bc:04X} (should be 0xAA10)")

    # Execute PUSH BC
    cpu.step()
    stack_low = cpu.memory.read_byte(0xDFEE)
    stack_high = cpu.memory.read_byte(0xDFEF)
    print(f"\nAfter PUSH BC:")
    print(f"  SP=0x{cpu.registers._sp:04X}")
    print(f"  Stack [0xDFEE]=0x{stack_low:02X} (should be 0x10 - low byte of BC)")
    print(f"  Stack [0xDFEF]=0x{stack_high:02X} (should be 0xAA - high byte of BC)")

    # Execute POP AF
    cpu.step()
    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)

    print(f"\nAfter POP AF:")
    print(f"  A=0x{a:02X} (should be 0xAA)")
    print(f"  F=0x{f:02X} (should be 0x10)")
    print(f"  Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
    print(f"  Expected: Z=0 N=0 H=0 C=1")

    if a != 0xAA:
        print(f"\n*** FAIL: A should be 0xAA, got 0x{a:02X} ***")
        return False

    if f != 0x10:
        print(f"\n*** FAIL: F should be 0x10, got 0x{f:02X} ***")
        print(f"  This means POP AF is not correctly setting flags from stack value!")
        return False

    # Now test INC SP to see if it preserves this
    print(f"\n--- Testing INC SP after POP AF ---")
    cpu.memory.write_byte(0x0106, 0x31)  # LD SP,$1234
    cpu.memory.write_byte(0x0107, 0x34)
    cpu.memory.write_byte(0x0108, 0x12)
    cpu.memory.write_byte(0x0109, 0x33)  # INC SP
    cpu.memory.write_byte(0x010A, 0x76)  # HALT

    cpu.registers._pc = 0x0106

    # LD SP
    cpu.step()
    sp_before = cpu.registers._sp
    f_before = get_f_register(cpu.registers.flags)

    # INC SP
    cpu.step()
    sp_after = cpu.registers._sp
    f_after = get_f_register(cpu.registers.flags)

    print(f"Before INC SP: SP=0x{sp_before:04X}, F=0x{f_before:02X}")
    print(f"After INC SP:  SP=0x{sp_after:04X}, F=0x{f_after:02X}")

    if f_after != f_before:
        print(f"\n*** FAIL: INC SP changed F from 0x{f_before:02X} to 0x{f_after:02X} ***")
        return False

    print("\n" + "=" * 80)
    print("TEST PASSED!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_push_pop_c_only()
    if not success:
        sys.exit(1)
