"""
Test that PC is correctly incremented for opcodes 0xE8 and 0xF8

These are 2-byte instructions:
- 0xE8: ADD SP,n
- 0xF8: LD HL,SP+n
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_e8_pc_increment():
    """Test PC increment for ADD SP,n (0xE8)"""
    cpu = CPU()

    # Write instruction: ADD SP,5 at address 0x0000
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,n
    cpu.memory.write_byte(0x0001, 0x05)  # n = 5
    cpu.memory.write_byte(0x0002, 0x00)  # NOP (next instruction)

    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xFFF0

    print("Test: ADD SP,n (0xE8)")
    print(f"Before: PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}")

    cpu.step()

    print(f"After:  PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}")

    if cpu.registers._pc == 0x0002:
        print("PASS: PC correctly incremented by 2")
        return True
    else:
        print(f"FAIL: PC should be 0x0002, but is 0x{cpu.registers._pc:04X}")
        return False

def test_f8_pc_increment():
    """Test PC increment for LD HL,SP+n (0xF8)"""
    cpu = CPU()

    # Write instruction: LD HL,SP+5 at address 0x0000
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+n
    cpu.memory.write_byte(0x0001, 0x05)  # n = 5
    cpu.memory.write_byte(0x0002, 0x00)  # NOP (next instruction)

    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xFFF0

    print("\nTest: LD HL,SP+n (0xF8)")
    print(f"Before: PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}, HL=0x{cpu.registers.hl:04X}")

    cpu.step()

    print(f"After:  PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}, HL=0x{cpu.registers.hl:04X}")

    if cpu.registers._pc == 0x0002:
        print("PASS: PC correctly incremented by 2")
        return True
    else:
        print(f"FAIL: PC should be 0x0002, but is 0x{cpu.registers._pc:04X}")
        return False

if __name__ == "__main__":
    result1 = test_e8_pc_increment()
    result2 = test_f8_pc_increment()

    print("\n" + "=" * 60)
    if result1 and result2:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
