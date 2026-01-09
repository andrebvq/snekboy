"""
Test exact sequence used in Blargg test 03 framework
This replicates the pattern: PUSH BC / POP AF -> Execute SP/HL ops -> Checksum
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

def checksum_registers(cpu):
    """Calculate simple checksum of AF, BC, DE, HL, SP like Blargg tests"""
    a = cpu.registers._a
    f = get_f_register(cpu.registers.flags)
    b = cpu.registers._b
    c = cpu.registers._c
    d = cpu.registers._d
    e = cpu.registers._e
    h = cpu.registers._h
    l = cpu.registers._l
    sp = cpu.registers._sp

    # Simple XOR checksum
    checksum = a ^ f ^ b ^ c ^ d ^ e ^ h ^ l ^ (sp >> 8) ^ (sp & 0xFF)
    return checksum

def test_sequence_1():
    """Test sequence: Set F=$F0, ADD SP,$FF, checksum"""
    cpu = CPU()

    print("Test 1: F=$F0, ADD SP,$FF with SP=$00FF")
    print("-" * 60)

    # Setup code in RAM at 0xC000
    addr = 0xC000
    cpu.memory.write_byte(addr + 0, 0x01)  # LD BC,$AAF0
    cpu.memory.write_byte(addr + 1, 0xF0)
    cpu.memory.write_byte(addr + 2, 0xAA)
    cpu.memory.write_byte(addr + 3, 0xC5)  # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)  # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)  # LD SP,$00FF
    cpu.memory.write_byte(addr + 6, 0xFF)
    cpu.memory.write_byte(addr + 7, 0x00)
    cpu.memory.write_byte(addr + 8, 0xE8)  # ADD SP,$FF
    cpu.memory.write_byte(addr + 9, 0xFF)
    cpu.memory.write_byte(addr + 10, 0x76) # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute sequence
    for i in range(6):
        cpu.step()

    print(f"  After sequence:")
    print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"    SP=0x{cpu.registers._sp:04X}")
    print(f"    Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

    # Verify
    assert cpu.registers._a == 0xAA, f"A should be 0xAA, got 0x{cpu.registers._a:02X}"
    assert cpu.registers._sp == 0x00FE, f"SP should be 0x00FE, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == True, "Z should be preserved (1)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == True, "H should be 1"
    assert cpu.registers.flags.carry == True, "C should be 1"

    checksum = checksum_registers(cpu)
    print(f"    Checksum: 0x{checksum:02X}")
    print("  PASS")

def test_sequence_2():
    """Test sequence: Set F=$00, LD HL,SP+$05, checksum"""
    cpu = CPU()

    print("\nTest 2: F=$00, LD HL,SP+$05 with SP=$1000")
    print("-" * 60)

    # Setup code in RAM at 0xC000
    addr = 0xC000
    cpu.memory.write_byte(addr + 0, 0x01)  # LD BC,$BB00
    cpu.memory.write_byte(addr + 1, 0x00)
    cpu.memory.write_byte(addr + 2, 0xBB)
    cpu.memory.write_byte(addr + 3, 0xC5)  # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)  # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)  # LD SP,$1000
    cpu.memory.write_byte(addr + 6, 0x00)
    cpu.memory.write_byte(addr + 7, 0x10)
    cpu.memory.write_byte(addr + 8, 0xF8)  # LD HL,SP+$05
    cpu.memory.write_byte(addr + 9, 0x05)
    cpu.memory.write_byte(addr + 10, 0x76) # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute sequence
    for i in range(6):
        cpu.step()

    print(f"  After sequence:")
    print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"    HL=0x{cpu.registers.hl:04X}")
    print(f"    Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

    # Verify
    assert cpu.registers._a == 0xBB, f"A should be 0xBB, got 0x{cpu.registers._a:02X}"
    assert cpu.registers.hl == 0x1005, f"HL should be 0x1005, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == False, "Z should be preserved (0)"
    assert cpu.registers.flags.subtract == False, "N should be 0"
    assert cpu.registers.flags.half_carry == False, "H should be 0"
    assert cpu.registers.flags.carry == False, "C should be 0"

    checksum = checksum_registers(cpu)
    print(f"    Checksum: 0x{checksum:02X}")
    print("  PASS")

def test_sequence_3():
    """Test chained operations with flag preservation"""
    cpu = CPU()

    print("\nTest 3: Chained operations - F=$F0, INC SP, ADD SP,$FF, DEC SP")
    print("-" * 60)

    # Setup code in RAM at 0xC000
    addr = 0xC000
    cpu.memory.write_byte(addr + 0, 0x01)  # LD BC,$CCF0
    cpu.memory.write_byte(addr + 1, 0xF0)
    cpu.memory.write_byte(addr + 2, 0xCC)
    cpu.memory.write_byte(addr + 3, 0xC5)  # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)  # POP AF
    cpu.memory.write_byte(addr + 5, 0x31)  # LD SP,$FF00
    cpu.memory.write_byte(addr + 6, 0x00)
    cpu.memory.write_byte(addr + 7, 0xFF)
    cpu.memory.write_byte(addr + 8, 0x33)  # INC SP
    cpu.memory.write_byte(addr + 9, 0xE8)  # ADD SP,$FF
    cpu.memory.write_byte(addr + 10, 0xFF)
    cpu.memory.write_byte(addr + 11, 0x3B) # DEC SP
    cpu.memory.write_byte(addr + 12, 0x76) # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute sequence
    for i in range(8):
        cpu.step()

    print(f"  After sequence:")
    print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"    SP=0x{cpu.registers._sp:04X}")
    print(f"    Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

    # Trace: SP starts at $FF00
    # INC SP -> $FF01
    # ADD SP,$FF -> $FF00 (also sets H=1, C=1)
    # DEC SP -> $FEFF

    assert cpu.registers._a == 0xCC
    assert cpu.registers._sp == 0xFEFF, f"SP should be 0xFEFF, got 0x{cpu.registers._sp:04X}"
    # Z should be preserved through all operations
    assert cpu.registers.flags.zero == True, "Z should be preserved (1)"
    # N should be 0 from ADD SP
    assert cpu.registers.flags.subtract == False, "N should be 0"
    # H and C set by ADD SP,$FF with $FF01 low byte
    assert cpu.registers.flags.half_carry == True, "H should be 1"
    assert cpu.registers.flags.carry == True, "C should be 1"

    checksum = checksum_registers(cpu)
    print(f"    Checksum: 0x{checksum:02X}")
    print("  PASS")

def test_sequence_4():
    """Test ADD HL,SP with Z preservation and N reset"""
    cpu = CPU()

    print("\nTest 4: F=$F0 (Z=1,N=1), ADD HL,SP (should preserve Z, reset N)")
    print("-" * 60)

    # Setup code in RAM at 0xC000
    addr = 0xC000
    cpu.memory.write_byte(addr + 0, 0x01)  # LD BC,$DDF0
    cpu.memory.write_byte(addr + 1, 0xF0)
    cpu.memory.write_byte(addr + 2, 0xDD)
    cpu.memory.write_byte(addr + 3, 0xC5)  # PUSH BC
    cpu.memory.write_byte(addr + 4, 0xF1)  # POP AF
    cpu.memory.write_byte(addr + 5, 0x21)  # LD HL,$1000
    cpu.memory.write_byte(addr + 6, 0x00)
    cpu.memory.write_byte(addr + 7, 0x10)
    cpu.memory.write_byte(addr + 8, 0x31)  # LD SP,$2000
    cpu.memory.write_byte(addr + 9, 0x00)
    cpu.memory.write_byte(addr + 10, 0x20)
    cpu.memory.write_byte(addr + 11, 0x39) # ADD HL,SP
    cpu.memory.write_byte(addr + 12, 0x76) # HALT

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute sequence
    for i in range(7):
        cpu.step()

    print(f"  After sequence:")
    print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"    HL=0x{cpu.registers.hl:04X}")
    print(f"    Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")

    assert cpu.registers._a == 0xDD
    assert cpu.registers.hl == 0x3000, f"HL should be 0x3000, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == True, "Z should be preserved (1)"
    assert cpu.registers.flags.subtract == False, "N should be RESET to 0"
    assert cpu.registers.flags.half_carry == False, "H should be 0"
    assert cpu.registers.flags.carry == False, "C should be 0"

    checksum = checksum_registers(cpu)
    print(f"    Checksum: 0x{checksum:02X}")
    print("  PASS")

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Blargg test 03 framework sequences")
    print("=" * 80)

    test_sequence_1()
    test_sequence_2()
    test_sequence_3()
    test_sequence_4()

    print()
    print("=" * 80)
    print("ALL INTEGRATION TESTS PASSED!")
    print("All SP/HL operations work correctly in chained sequences")
    print("=" * 80)
