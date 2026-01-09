"""
Test LD (nn),SP in chained context with INC SP, initial F=$F0, and CRC calculation
This addresses recommendation #1 - boundary SP values with full chain
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

def simple_crc(bytes_list):
    """Simple XOR-based CRC for comparison"""
    crc = 0
    for b in bytes_list:
        crc ^= b
    return crc

def test_ld_sp_chained():
    print("Testing LD (nn),SP in chained context with INC SP and CRC")
    print("=" * 80)

    # Test critical boundary cases with F=$F0
    test_cases = [
        (0x0000, 0x0001, "zero boundary"),
        (0xFFFF, 0x0000, "wrap boundary"),
        (0x7FFF, 0x8000, "sign boundary"),
        (0x8000, 0x8001, "high bit set"),
        (0x00FF, 0x0100, "low byte overflow"),
    ]

    for sp_initial, sp_expected, description in test_cases:
        cpu = CPU()

        print(f"\nTest: {description} - SP=0x{sp_initial:04X} -> 0x{sp_expected:04X}")
        print("-" * 60)

        addr = 0xC100
        # Set initial F=$F0 via PUSH BC / POP AF
        cpu.memory.write_byte(addr + 0, 0x01)   # LD BC,$AAF0
        cpu.memory.write_byte(addr + 1, 0xF0)
        cpu.memory.write_byte(addr + 2, 0xAA)
        cpu.memory.write_byte(addr + 3, 0xC5)   # PUSH BC
        cpu.memory.write_byte(addr + 4, 0xF1)   # POP AF (A=$AA, F=$F0)

        # Set SP to initial value
        cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,nn
        cpu.memory.write_byte(addr + 6, sp_initial & 0xFF)
        cpu.memory.write_byte(addr + 7, (sp_initial >> 8) & 0xFF)

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

        # Execute the sequence
        for i in range(10):
            cpu.step()

        # Check results
        a = cpu.registers._a
        f = get_f_register(cpu.registers.flags)
        sp_final = cpu.registers._sp

        # Read saved SP values
        sp_orig_low = cpu.memory.read_byte(0xC000)
        sp_orig_high = cpu.memory.read_byte(0xC001)
        sp_new_low = cpu.memory.read_byte(0xC002)
        sp_new_high = cpu.memory.read_byte(0xC003)

        print(f"  After execution:")
        print(f"    A=0x{a:02X} F=0x{f:02X} (Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)})")
        print(f"    SP=0x{sp_final:04X} (expected 0x{sp_expected:04X})")
        print(f"  Original SP saved: [0xC000]=0x{sp_orig_low:02X}, [0xC001]=0x{sp_orig_high:02X}")
        print(f"  New SP saved:      [0xC002]=0x{sp_new_low:02X}, [0xC003]=0x{sp_new_high:02X}")

        # Calculate CRC (XOR of temp+2 bytes and AF)
        crc = simple_crc([sp_new_low, sp_new_high, a, f])
        print(f"  Simple CRC (new_SP_low ^ new_SP_high ^ A ^ F): 0x{crc:02X}")

        # Verify F unchanged (should still be $F0)
        if f != 0xF0:
            print(f"  *** FAIL: F changed from 0xF0 to 0x{f:02X} ***")
            return False

        # Verify SP correct
        if sp_final != sp_expected:
            print(f"  *** FAIL: SP incorrect - expected 0x{sp_expected:04X}, got 0x{sp_final:04X} ***")
            return False

        # Verify original SP saved correctly
        sp_orig_reconstructed = sp_orig_low | (sp_orig_high << 8)
        if sp_orig_reconstructed != sp_initial:
            print(f"  *** FAIL: Original SP saved incorrectly ***")
            print(f"      Expected: 0x{sp_initial:04X}")
            print(f"      Got:      0x{sp_orig_reconstructed:04X}")
            return False

        # Verify new SP saved correctly
        sp_new_reconstructed = sp_new_low | (sp_new_high << 8)
        if sp_new_reconstructed != sp_expected:
            print(f"  *** FAIL: New SP saved incorrectly ***")
            print(f"      Expected: 0x{sp_expected:04X}")
            print(f"      Got:      0x{sp_new_reconstructed:04X}")
            print(f"      Bytes: low=0x{sp_new_low:02X}, high=0x{sp_new_high:02X}")
            return False

        print("  PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("LD (nn),SP works correctly in chained context with INC SP")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_ld_sp_chained()
    if not success:
        sys.exit(1)
