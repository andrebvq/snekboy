"""
Replicate the EXACT Blargg test 03 pattern:
1. PUSH BC / POP AF to set initial flags ($00 or $F0)
2. Save original SP with LD (temp),SP
3. Execute INC SP
4. Save new SP with LD (temp+2),SP
5. Checksum the result

This tests the COMPLETE chain including any subtle interactions
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

def calculate_checksum(cpu, sp_orig_addr, sp_new_addr):
    """Calculate checksum like Blargg: XOR of all bytes"""
    # Get SP bytes
    sp_orig_low = cpu.memory.read_byte(sp_orig_addr)
    sp_orig_high = cpu.memory.read_byte(sp_orig_addr + 1)
    sp_new_low = cpu.memory.read_byte(sp_new_addr)
    sp_new_high = cpu.memory.read_byte(sp_new_addr + 1)

    # Get register values
    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    b = cpu.registers._b
    c = cpu.registers._c

    # Simple XOR checksum
    checksum = a ^ f ^ b ^ c ^ sp_orig_low ^ sp_orig_high ^ sp_new_low ^ sp_new_high
    return checksum, (sp_orig_low, sp_orig_high, sp_new_low, sp_new_high)

def test_inc_sp_exact_pattern():
    cpu = CPU()

    print("Testing INC SP with EXACT Blargg test 03 pattern")
    print("=" * 80)

    # Test case: SP=$0000, F=$00 -> INC SP -> SP=$0001
    print("\nTest 1: INC SP with SP=$0000, F=$00")
    print("-" * 60)

    addr = 0xC100
    # Set BC to $AA00 (will become AF=$AA00 after POP)
    cpu.memory.write_byte(addr + 0, 0x01)   # LD BC,$00AA
    cpu.memory.write_byte(addr + 1, 0x00)
    cpu.memory.write_byte(addr + 2, 0xAA)
    # PUSH BC
    cpu.memory.write_byte(addr + 3, 0xC5)
    # POP AF (now A=$AA, F=$00)
    cpu.memory.write_byte(addr + 4, 0xF1)
    # Set SP to $0000
    cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,$0000
    cpu.memory.write_byte(addr + 6, 0x00)
    cpu.memory.write_byte(addr + 7, 0x00)
    # Save original SP to $C000
    cpu.memory.write_byte(addr + 8, 0x08)   # LD ($C000),SP
    cpu.memory.write_byte(addr + 9, 0x00)
    cpu.memory.write_byte(addr + 10, 0xC0)
    # INC SP
    cpu.memory.write_byte(addr + 11, 0x33)
    # Save new SP to $C002
    cpu.memory.write_byte(addr + 12, 0x08)  # LD ($C002),SP
    cpu.memory.write_byte(addr + 13, 0x02)
    cpu.memory.write_byte(addr + 14, 0xC0)
    # HALT
    cpu.memory.write_byte(addr + 15, 0x76)

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute the sequence
    for i in range(9):
        cpu.step()

    # Check results
    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    sp = cpu.registers._sp

    sp_orig_low = cpu.memory.read_byte(0xC000)
    sp_orig_high = cpu.memory.read_byte(0xC001)
    sp_new_low = cpu.memory.read_byte(0xC002)
    sp_new_high = cpu.memory.read_byte(0xC003)

    print(f"  After execution:")
    print(f"    A=0x{a:02X} (expected 0xAA)")
    print(f"    F=0x{f:02X} (expected 0x00)")
    print(f"    SP=0x{sp:04X} (expected 0x0001)")
    print(f"  Original SP saved: [0xC000]=0x{sp_orig_low:02X}, [0xC001]=0x{sp_orig_high:02X}")
    print(f"  New SP saved:      [0xC002]=0x{sp_new_low:02X}, [0xC003]=0x{sp_new_high:02X}")

    checksum, _ = calculate_checksum(cpu, 0xC000, 0xC002)
    print(f"  Checksum: 0x{checksum:02X}")

    # Verify
    assert a == 0xAA, f"A should be 0xAA, got 0x{a:02X}"
    assert f == 0x00, f"F should be 0x00, got 0x{f:02X}"
    assert sp == 0x0001, f"SP should be 0x0001, got 0x{sp:04X}"
    assert sp_orig_low == 0x00 and sp_orig_high == 0x00, "Original SP incorrect"
    assert sp_new_low == 0x01 and sp_new_high == 0x00, f"New SP incorrect: got {sp_new_high:02X}{sp_new_low:02X}"

    print("  PASS")

    # Test case 2: SP=$FFFF, F=$F0 -> INC SP -> SP=$0000
    # Use fresh CPU instance
    cpu = CPU()

    print("\nTest 2: INC SP with SP=$FFFF, F=$F0")
    print("-" * 60)

    addr = 0xC100
    # Set BC to $BBF0 (will become AF=$BBF0)
    cpu.memory.write_byte(addr + 0, 0x01)
    cpu.memory.write_byte(addr + 1, 0xF0)
    cpu.memory.write_byte(addr + 2, 0xBB)
    cpu.memory.write_byte(addr + 3, 0xC5)   # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)   # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,$FFFF
    cpu.memory.write_byte(addr + 6, 0xFF)
    cpu.memory.write_byte(addr + 7, 0xFF)
    cpu.memory.write_byte(addr + 8, 0x08)   # LD ($C000),SP
    cpu.memory.write_byte(addr + 9, 0x00)
    cpu.memory.write_byte(addr + 10, 0xC0)
    cpu.memory.write_byte(addr + 11, 0x33)  # INC SP
    cpu.memory.write_byte(addr + 12, 0x08)  # LD ($C002),SP
    cpu.memory.write_byte(addr + 13, 0x02)
    cpu.memory.write_byte(addr + 14, 0xC0)
    cpu.memory.write_byte(addr + 15, 0x76)  # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    for i in range(9):
        cpu.step()

    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    sp = cpu.registers._sp

    sp_orig_low = cpu.memory.read_byte(0xC000)
    sp_orig_high = cpu.memory.read_byte(0xC001)
    sp_new_low = cpu.memory.read_byte(0xC002)
    sp_new_high = cpu.memory.read_byte(0xC003)

    print(f"  After execution:")
    print(f"    A=0x{a:02X} (expected 0xBB)")
    print(f"    F=0x{f:02X} (expected 0xF0)")
    print(f"    SP=0x{sp:04X} (expected 0x0000)")
    print(f"  Original SP saved: [0xC000]=0x{sp_orig_low:02X}, [0xC001]=0x{sp_orig_high:02X}")
    print(f"  New SP saved:      [0xC002]=0x{sp_new_low:02X}, [0xC003]=0x{sp_new_high:02X}")

    checksum, _ = calculate_checksum(cpu, 0xC000, 0xC002)
    print(f"  Checksum: 0x{checksum:02X}")

    assert a == 0xBB, f"A should be 0xBB, got 0x{a:02X}"
    assert f == 0xF0, f"F should be 0xF0, got 0x{f:02X}"
    assert sp == 0x0000, f"SP should be 0x0000, got 0x{sp:04X}"
    assert sp_orig_low == 0xFF and sp_orig_high == 0xFF, "Original SP incorrect"
    assert sp_new_low == 0x00 and sp_new_high == 0x00, "New SP incorrect"

    print("  PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("INC SP works correctly in exact Blargg pattern")
    print("=" * 80)

if __name__ == "__main__":
    test_inc_sp_exact_pattern()
