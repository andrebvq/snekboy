"""
Test ADD SP,e (0xE8) and LD HL,SP+e (0xF8) with exact Blargg pattern
These are specifically mentioned in the standalone test output
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

def test_add_sp_pattern():
    """Test ADD SP,$FF with exact Blargg pattern"""
    cpu = CPU()

    print("Testing ADD SP,$FF with exact Blargg pattern")
    print("=" * 80)

    # Test: ADD SP,$FF (e=-1) with SP=$00FF, F=$00
    print("\nTest 1: ADD SP,$FF with SP=$00FF, F=$00")

    addr = 0xC100
    # Set BC to $AA00 -> AF=$AA00
    cpu.memory.write_byte(addr + 0, 0x01)   # LD BC,$00AA
    cpu.memory.write_byte(addr + 1, 0x00)
    cpu.memory.write_byte(addr + 2, 0xAA)
    cpu.memory.write_byte(addr + 3, 0xC5)   # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)   # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,$00FF
    cpu.memory.write_byte(addr + 6, 0xFF)
    cpu.memory.write_byte(addr + 7, 0x00)
    cpu.memory.write_byte(addr + 8, 0x08)   # LD ($C000),SP
    cpu.memory.write_byte(addr + 9, 0x00)
    cpu.memory.write_byte(addr + 10, 0xC0)
    cpu.memory.write_byte(addr + 11, 0xE8)  # ADD SP,$FF
    cpu.memory.write_byte(addr + 12, 0xFF)
    cpu.memory.write_byte(addr + 13, 0x08)  # LD ($C002),SP
    cpu.memory.write_byte(addr + 14, 0x02)
    cpu.memory.write_byte(addr + 15, 0xC0)
    cpu.memory.write_byte(addr + 16, 0x76)  # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    for i in range(10):
        cpu.step()

    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    sp = cpu.registers._sp
    z = int(cpu.registers.flags.zero)
    n = int(cpu.registers.flags.subtract)
    h = int(cpu.registers.flags.half_carry)
    c = int(cpu.registers.flags.carry)

    sp_orig_low = cpu.memory.read_byte(0xC000)
    sp_orig_high = cpu.memory.read_byte(0xC001)
    sp_new_low = cpu.memory.read_byte(0xC002)
    sp_new_high = cpu.memory.read_byte(0xC003)

    print(f"  After execution:")
    print(f"    A=0x{a:02X} F=0x{f:02X}")
    print(f"    Flags: Z={z} N={n} H={h} C={c}")
    print(f"    SP=0x{sp:04X} (expected 0x00FE)")
    print(f"  Original SP: [0xC000]=0x{sp_orig_low:02X}, [0xC001]=0x{sp_orig_high:02X}")
    print(f"  New SP:      [0xC002]=0x{sp_new_low:02X}, [0xC003]=0x{sp_new_high:02X}")

    assert a == 0xAA
    assert z == 0, "Z should be preserved (0)"
    assert n == 0, "N should be 0"
    assert h == 1, "H should be 1"
    assert c == 1, "C should be 1"
    assert sp == 0x00FE, f"SP should be 0x00FE, got 0x{sp:04X}"
    assert sp_orig_low == 0xFF and sp_orig_high == 0x00
    assert sp_new_low == 0xFE and sp_new_high == 0x00, f"New SP should be FE 00, got {sp_new_high:02X} {sp_new_low:02X}"

    print("  PASS")

def test_ld_hl_sp_pattern():
    """Test LD HL,SP+$FF with exact Blargg pattern"""
    cpu = CPU()

    print("\nTesting LD HL,SP+$FF with exact Blargg pattern")
    print("=" * 80)

    # Test: LD HL,SP+$FF with SP=$00FF, F=$F0
    print("\nTest 1: LD HL,SP+$FF with SP=$00FF, F=$F0")

    addr = 0xC100
    # Set BC to $BBF0 -> AF=$BBF0
    cpu.memory.write_byte(addr + 0, 0x01)   # LD BC,$F0BB
    cpu.memory.write_byte(addr + 1, 0xF0)
    cpu.memory.write_byte(addr + 2, 0xBB)
    cpu.memory.write_byte(addr + 3, 0xC5)   # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)   # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)   # LD SP,$00FF
    cpu.memory.write_byte(addr + 6, 0xFF)
    cpu.memory.write_byte(addr + 7, 0x00)
    cpu.memory.write_byte(addr + 8, 0xF8)   # LD HL,SP+$FF
    cpu.memory.write_byte(addr + 9, 0xFF)
    cpu.memory.write_byte(addr + 10, 0x76)  # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    for i in range(7):
        cpu.step()

    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    hl = cpu.registers.hl
    sp = cpu.registers._sp
    z = int(cpu.registers.flags.zero)
    n = int(cpu.registers.flags.subtract)
    h = int(cpu.registers.flags.half_carry)
    c = int(cpu.registers.flags.carry)

    print(f"  After execution:")
    print(f"    A=0x{a:02X} F=0x{f:02X}")
    print(f"    Flags: Z={z} N={n} H={h} C={c}")
    print(f"    HL=0x{hl:04X} (expected 0x00FE)")
    print(f"    SP=0x{sp:04X} (expected 0x00FF - unchanged)")

    assert a == 0xBB
    assert z == 1, "Z should be preserved (1)"
    assert n == 0, "N should be 0"
    assert h == 1, "H should be 1"
    assert c == 1, "C should be 1"
    assert hl == 0x00FE, f"HL should be 0x00FE, got 0x{hl:04X}"
    assert sp == 0x00FF, f"SP should be unchanged at 0x00FF, got 0x{sp:04X}"

    print("  PASS")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("ADD SP,e and LD HL,SP+e work correctly in exact Blargg pattern")
    print("=" * 80)

if __name__ == "__main__":
    test_add_sp_pattern()
    test_ld_hl_sp_pattern()
