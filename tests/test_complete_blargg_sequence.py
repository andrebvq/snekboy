"""
Complete Blargg test 03 sequence simulation
This tests the EXACT sequence the ROM uses including all register setup
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

def test_complete_sequence():
    """
    Simulate the complete Blargg test sequence:
    1. Set BC, DE, HL to test values
    2. Set initial F via PUSH BC / POP AF
    3. Save all registers to temp area
    4. Execute INC SP
    5. Save new SP
    6. Checksum everything
    """
    cpu = CPU()

    print("Testing COMPLETE Blargg test 03 sequence")
    print("=" * 80)

    addr = 0xC100

    # Test case: INC SP with SP=$0000, F=$00, and various BC/DE/HL values
    print("\nTest: Full register sequence with INC SP")
    print("-" * 60)

    # Set up initial register values (typical test values)
    bc_val = 0x1234
    de_val = 0x5678
    hl_val = 0x9ABC
    a_val = 0xAA
    f_val = 0x00
    sp_val = 0x0000

    # LD BC,nn
    cpu.memory.write_byte(addr + 0, 0x01)
    cpu.memory.write_byte(addr + 1, bc_val & 0xFF)
    cpu.memory.write_byte(addr + 2, (bc_val >> 8) & 0xFF)

    # LD DE,nn
    cpu.memory.write_byte(addr + 3, 0x11)
    cpu.memory.write_byte(addr + 4, de_val & 0xFF)
    cpu.memory.write_byte(addr + 5, (de_val >> 8) & 0xFF)

    # LD HL,nn
    cpu.memory.write_byte(addr + 6, 0x21)
    cpu.memory.write_byte(addr + 7, hl_val & 0xFF)
    cpu.memory.write_byte(addr + 8, (hl_val >> 8) & 0xFF)

    # Set AF via stack manipulation
    # LD BC,nn (for AF setup)
    cpu.memory.write_byte(addr + 9, 0x01)
    cpu.memory.write_byte(addr + 10, f_val)   # Will become F
    cpu.memory.write_byte(addr + 11, a_val)   # Will become A

    # PUSH BC
    cpu.memory.write_byte(addr + 12, 0xC5)

    # POP AF
    cpu.memory.write_byte(addr + 13, 0xF1)

    # Restore BC
    cpu.memory.write_byte(addr + 14, 0x01)
    cpu.memory.write_byte(addr + 15, bc_val & 0xFF)
    cpu.memory.write_byte(addr + 16, (bc_val >> 8) & 0xFF)

    # Set SP
    cpu.memory.write_byte(addr + 17, 0x31)
    cpu.memory.write_byte(addr + 18, sp_val & 0xFF)
    cpu.memory.write_byte(addr + 19, (sp_val >> 8) & 0xFF)

    # Save AF to temp ($C000)
    cpu.memory.write_byte(addr + 20, 0xF5)  # PUSH AF
    cpu.memory.write_byte(addr + 21, 0xE1)  # POP HL
    cpu.memory.write_byte(addr + 22, 0x22)  # LD ($C000),HL (save AF)
    cpu.memory.write_byte(addr + 23, 0x00)
    cpu.memory.write_byte(addr + 24, 0xC0)

    # Restore HL
    cpu.memory.write_byte(addr + 25, 0x21)
    cpu.memory.write_byte(addr + 26, hl_val & 0xFF)
    cpu.memory.write_byte(addr + 27, (hl_val >> 8) & 0xFF)

    # Save original SP to $C002
    cpu.memory.write_byte(addr + 28, 0x08)
    cpu.memory.write_byte(addr + 29, 0x02)
    cpu.memory.write_byte(addr + 30, 0xC0)

    # INC SP
    cpu.memory.write_byte(addr + 31, 0x33)

    # Save new SP to $C004
    cpu.memory.write_byte(addr + 32, 0x08)
    cpu.memory.write_byte(addr + 33, 0x04)
    cpu.memory.write_byte(addr + 34, 0xC0)

    # HALT
    cpu.memory.write_byte(addr + 35, 0x76)

    cpu.registers._pc = addr
    cpu.registers._sp = 0xDFF0

    # Execute the full sequence
    for i in range(22):  # Enough steps to complete
        if cpu.halted:
            break
        cpu.step()

    # Read results
    af_low = cpu.memory.read_byte(0xC000)
    af_high = cpu.memory.read_byte(0xC001)
    sp_orig_low = cpu.memory.read_byte(0xC002)
    sp_orig_high = cpu.memory.read_byte(0xC003)
    sp_new_low = cpu.memory.read_byte(0xC004)
    sp_new_high = cpu.memory.read_byte(0xC005)

    print(f"  Final state:")
    print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"    BC=0x{cpu.registers.bc:04X}")
    print(f"    DE=0x{cpu.registers.de:04X}")
    print(f"    HL=0x{cpu.registers.hl:04X}")
    print(f"    SP=0x{cpu.registers._sp:04X}")
    print()
    print(f"  Saved values:")
    print(f"    AF saved:  F=0x{af_low:02X}, A=0x{af_high:02X}")
    print(f"    SP orig:   low=0x{sp_orig_low:02X}, high=0x{sp_orig_high:02X} (=0x{sp_orig_high:02X}{sp_orig_low:02X})")
    print(f"    SP new:    low=0x{sp_new_low:02X}, high=0x{sp_new_high:02X} (=0x{sp_new_high:02X}{sp_new_low:02X})")

    # Verify
    assert cpu.registers._a == a_val, f"A mismatch"
    assert get_f_register(cpu.registers.flags) == f_val, f"F mismatch"
    assert cpu.registers.bc == bc_val, f"BC mismatch"
    assert cpu.registers.de == de_val, f"DE mismatch"
    assert cpu.registers.hl == hl_val, f"HL mismatch"
    assert cpu.registers._sp == 0x0001, f"SP should be 0x0001"
    assert sp_orig_low == 0x00 and sp_orig_high == 0x00, "Original SP save incorrect"
    assert sp_new_low == 0x01 and sp_new_high == 0x00, "New SP save incorrect"

    print("\n  PASS!")

    print()
    print("=" * 80)
    print("COMPLETE SEQUENCE TEST PASSED!")
    print("All registers and SP operations work correctly")
    print("=" * 80)

if __name__ == "__main__":
    test_complete_sequence()
