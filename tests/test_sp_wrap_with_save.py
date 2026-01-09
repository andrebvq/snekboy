"""
Test SP wrap from $FFFF to $0000 with memory save like Blargg test
This is hypothesis #3 - SP not wrapping correctly
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_sp_wrap_with_checksum():
    cpu = CPU()

    print("Testing SP wrap with LD (nn),SP save pattern (Blargg-style)")
    print("=" * 80)

    # Test pattern: Save original SP, INC SP, save new SP, compare bytes
    test_cases = [
        (0xFFFF, 0x0000),  # Wrap boundary
        (0x00FF, 0x0100),  # Low byte overflow
        (0x0FFF, 0x1000),  # Mid boundary
        (0x0000, 0x0001),  # From zero
    ]

    for sp_initial, sp_expected in test_cases:
        print(f"\nTest: SP=0x{sp_initial:04X} -> INC SP -> 0x{sp_expected:04X}")

        # Save original SP to $C000
        cpu.memory.write_byte(0x0000, 0x08)  # LD ($C000),SP
        cpu.memory.write_byte(0x0001, 0x00)
        cpu.memory.write_byte(0x0002, 0xC0)
        cpu.registers._pc = 0x0000
        cpu.registers._sp = sp_initial
        cpu.step()

        orig_low = cpu.memory.read_byte(0xC000)
        orig_high = cpu.memory.read_byte(0xC001)
        print(f"  Original SP saved: [0xC000]=0x{orig_low:02X}, [0xC001]=0x{orig_high:02X}")

        # INC SP
        cpu.memory.write_byte(0x0003, 0x33)  # INC SP
        cpu.registers._pc = 0x0003
        cpu.step()

        sp_after = cpu.registers._sp
        print(f"  After INC SP: SP=0x{sp_after:04X} (expected 0x{sp_expected:04X})")

        if sp_after != sp_expected:
            print(f"  *** FAIL: SP wrap incorrect! ***")
            return False

        # Save new SP to $C002
        cpu.memory.write_byte(0x0004, 0x08)  # LD ($C002),SP
        cpu.memory.write_byte(0x0005, 0x02)
        cpu.memory.write_byte(0x0006, 0xC0)
        cpu.registers._pc = 0x0004
        cpu.step()

        new_low = cpu.memory.read_byte(0xC002)
        new_high = cpu.memory.read_byte(0xC003)
        print(f"  New SP saved: [0xC002]=0x{new_low:02X}, [0xC003]=0x{new_high:02X}")

        # Verify bytes match expected
        expected_low = sp_expected & 0xFF
        expected_high = (sp_expected >> 8) & 0xFF

        if new_low != expected_low or new_high != expected_high:
            print(f"  *** FAIL: Saved bytes incorrect! ***")
            print(f"      Expected: low=0x{expected_low:02X}, high=0x{expected_high:02X}")
            print(f"      Got:      low=0x{new_low:02X}, high=0x{new_high:02X}")
            return False

        print(f"  PASS")

    # Test with checksum calculation like Blargg
    print(f"\nTest: Checksum pattern like Blargg test 03")
    cpu.registers._sp = 0xFFFF

    # INC SP
    cpu.memory.write_byte(0x0000, 0x33)
    cpu.registers._pc = 0x0000
    cpu.step()

    # Save SP
    cpu.memory.write_byte(0x0001, 0x08)
    cpu.memory.write_byte(0x0002, 0x00)
    cpu.memory.write_byte(0x0003, 0xC0)
    cpu.registers._pc = 0x0001
    cpu.step()

    # Calculate simple checksum (XOR of bytes)
    sp_low = cpu.memory.read_byte(0xC000)
    sp_high = cpu.memory.read_byte(0xC001)
    checksum = sp_low ^ sp_high

    print(f"  SP after INC: 0x{cpu.registers._sp:04X}")
    print(f"  Saved bytes: low=0x{sp_low:02X}, high=0x{sp_high:02X}")
    print(f"  Checksum (low XOR high): 0x{checksum:02X}")

    if cpu.registers._sp == 0x0000 and sp_low == 0x00 and sp_high == 0x00:
        print(f"  PASS")
    else:
        print(f"  FAIL")
        return False

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("SP wrapping and save pattern work correctly")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_sp_wrap_with_checksum()
    if not success:
        sys.exit(1)
