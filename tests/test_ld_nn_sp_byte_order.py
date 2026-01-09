"""
Test that LD (nn),SP writes SP in correct byte order (little-endian)
This is hypothesis #1 - highest probability for "01" error
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_ld_nn_sp_byte_order():
    cpu = CPU()

    print("Testing LD (nn),SP byte order (little-endian)")
    print("=" * 80)

    # Test 1: LD (nn),SP with SP=$1234
    print("\nTest 1: LD ($C000),SP with SP=$1234")
    cpu.memory.write_byte(0x0000, 0x08)  # LD (nn),SP
    cpu.memory.write_byte(0x0001, 0x00)  # nn low byte = $00
    cpu.memory.write_byte(0x0002, 0xC0)  # nn high byte = $C0
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x1234

    cpu.step()

    low_byte = cpu.memory.read_byte(0xC000)
    high_byte = cpu.memory.read_byte(0xC001)

    print(f"  SP before: 0x{0x1234:04X}")
    print(f"  Memory [0xC000] = 0x{low_byte:02X} (should be 0x34 - SP low byte)")
    print(f"  Memory [0xC001] = 0x{high_byte:02X} (should be 0x12 - SP high byte)")

    if low_byte == 0x34 and high_byte == 0x12:
        print("  PASS: Correct little-endian byte order")
    else:
        print(f"  FAIL: Expected [0xC000]=0x34, [0xC001]=0x12")
        print(f"        Got      [0xC000]=0x{low_byte:02X}, [0xC001]=0x{high_byte:02X}")
        if low_byte == 0x12 and high_byte == 0x34:
            print("  *** BYTE ORDER SWAPPED (BIG-ENDIAN) - THIS IS THE BUG! ***")
        return False

    # Test 2: LD (nn),SP with SP=$0001 (after INC SP from $0000)
    print("\nTest 2: LD ($C000),SP with SP=$0001")
    cpu.memory.write_byte(0x0000, 0x08)  # LD (nn),SP
    cpu.memory.write_byte(0x0001, 0x00)
    cpu.memory.write_byte(0x0002, 0xC0)
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x0001

    cpu.step()

    low_byte = cpu.memory.read_byte(0xC000)
    high_byte = cpu.memory.read_byte(0xC001)

    print(f"  SP: 0x{0x0001:04X}")
    print(f"  Memory [0xC000] = 0x{low_byte:02X} (should be 0x01)")
    print(f"  Memory [0xC001] = 0x{high_byte:02X} (should be 0x00)")

    if low_byte == 0x01 and high_byte == 0x00:
        print("  PASS")
    else:
        print(f"  FAIL: Expected [0xC000]=0x01, [0xC001]=0x00")
        print(f"        Got      [0xC000]=0x{low_byte:02X}, [0xC001]=0x{high_byte:02X}")
        if low_byte == 0x00 and high_byte == 0x01:
            print("  *** BYTE ORDER SWAPPED - THIS IS THE BUG! ***")
        return False

    # Test 3: LD (nn),SP with SP=$0000 (boundary)
    print("\nTest 3: LD ($C000),SP with SP=$0000")
    cpu.memory.write_byte(0x0000, 0x08)
    cpu.memory.write_byte(0x0001, 0x00)
    cpu.memory.write_byte(0x0002, 0xC0)
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0x0000

    cpu.step()

    low_byte = cpu.memory.read_byte(0xC000)
    high_byte = cpu.memory.read_byte(0xC001)

    print(f"  SP: 0x{0x0000:04X}")
    print(f"  Memory [0xC000] = 0x{low_byte:02X} (should be 0x00)")
    print(f"  Memory [0xC001] = 0x{high_byte:02X} (should be 0x00)")

    if low_byte == 0x00 and high_byte == 0x00:
        print("  PASS")
    else:
        print(f"  FAIL")
        return False

    # Test 4: LD (nn),SP with SP=$FFFF (boundary)
    print("\nTest 4: LD ($C000),SP with SP=$FFFF")
    cpu.memory.write_byte(0x0000, 0x08)
    cpu.memory.write_byte(0x0001, 0x00)
    cpu.memory.write_byte(0x0002, 0xC0)
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xFFFF

    cpu.step()

    low_byte = cpu.memory.read_byte(0xC000)
    high_byte = cpu.memory.read_byte(0xC001)

    print(f"  SP: 0x{0xFFFF:04X}")
    print(f"  Memory [0xC000] = 0x{low_byte:02X} (should be 0xFF)")
    print(f"  Memory [0xC001] = 0x{high_byte:02X} (should be 0xFF)")

    if low_byte == 0xFF and high_byte == 0xFF:
        print("  PASS")
    else:
        print(f"  FAIL")
        return False

    # Test 5: Simulate Blargg test 03 pattern - INC SP then save
    print("\nTest 5: Blargg pattern - INC SP from $0000, then save with LD (nn),SP")
    # Set SP to $0000
    cpu.registers._sp = 0x0000

    # INC SP
    cpu.memory.write_byte(0x0000, 0x33)  # INC SP
    cpu.registers._pc = 0x0000
    cpu.step()

    sp_after_inc = cpu.registers._sp
    print(f"  After INC SP: SP = 0x{sp_after_inc:04X} (should be 0x0001)")

    # Save SP to memory
    cpu.memory.write_byte(0x0001, 0x08)  # LD (nn),SP
    cpu.memory.write_byte(0x0002, 0x00)
    cpu.memory.write_byte(0x0003, 0xC0)
    cpu.registers._pc = 0x0001
    cpu.step()

    low_byte = cpu.memory.read_byte(0xC000)
    high_byte = cpu.memory.read_byte(0xC001)

    print(f"  Saved to memory:")
    print(f"    [0xC000] = 0x{low_byte:02X} (should be 0x01 - low byte)")
    print(f"    [0xC001] = 0x{high_byte:02X} (should be 0x00 - high byte)")

    if low_byte == 0x01 and high_byte == 0x00:
        print("  PASS")
    else:
        print(f"  FAIL")
        if low_byte == 0x00 and high_byte == 0x01:
            print("  *** BYTE ORDER SWAPPED! ***")
        return False

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("LD (nn),SP uses correct little-endian byte order")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_ld_nn_sp_byte_order()
    if not success:
        sys.exit(1)
