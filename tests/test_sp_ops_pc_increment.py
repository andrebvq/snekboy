"""
Test that ADD SP,e and LD HL,SP+e correctly increment PC by 2
This checks point #1 from the latest analysis - THE CRITICAL BUG!
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_pc_increment():
    cpu = CPU()

    print("Testing PC increment for ADD SP,e and LD HL,SP+e")
    print("=" * 80)

    # Test 1: ADD SP,e should increment PC by 2 (opcode + operand)
    print("\nTest 1: ADD SP,$05 - PC should advance by 2")
    cpu.memory.write_byte(0x0100, 0xE8)  # ADD SP,e at 0x0100
    cpu.memory.write_byte(0x0101, 0x05)  # e = +5
    cpu.memory.write_byte(0x0102, 0x00)  # NOP (next instruction)

    cpu.registers._pc = 0x0100
    cpu.registers._sp = 0xDFF0

    print(f"  Before: PC=0x{cpu.registers._pc:04X}")
    cpu.step()
    print(f"  After:  PC=0x{cpu.registers._pc:04X} (should be 0x0102)")

    assert cpu.registers._pc == 0x0102, f"PC should be 0x0102, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDFF5, f"SP should be 0xDFF5, got 0x{cpu.registers._sp:04X}"
    print("  PASS: PC correctly incremented by 2")

    # Test 2: LD HL,SP+e should increment PC by 2
    print("\nTest 2: LD HL,SP+$03 - PC should advance by 2")
    cpu.memory.write_byte(0x0200, 0xF8)  # LD HL,SP+e at 0x0200
    cpu.memory.write_byte(0x0201, 0x03)  # e = +3
    cpu.memory.write_byte(0x0202, 0x00)  # NOP (next instruction)

    cpu.registers._pc = 0x0200
    cpu.registers._sp = 0xDFF0

    print(f"  Before: PC=0x{cpu.registers._pc:04X}")
    cpu.step()
    print(f"  After:  PC=0x{cpu.registers._pc:04X} (should be 0x0202)")

    assert cpu.registers._pc == 0x0202, f"PC should be 0x0202, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers.hl == 0xDFF3, f"HL should be 0xDFF3, got 0x{cpu.registers.hl:04X}"
    print("  PASS: PC correctly incremented by 2")

    # Test 3: ADD SP with negative offset
    print("\nTest 3: ADD SP,$FF (negative) - PC should advance by 2")
    cpu.memory.write_byte(0x0300, 0xE8)  # ADD SP,e at 0x0300
    cpu.memory.write_byte(0x0301, 0xFF)  # e = -1
    cpu.memory.write_byte(0x0302, 0x00)  # NOP (next instruction)

    cpu.registers._pc = 0x0300
    cpu.registers._sp = 0xDFF0

    print(f"  Before: PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}")
    cpu.step()
    print(f"  After:  PC=0x{cpu.registers._pc:04X} (should be 0x0302), SP=0x{cpu.registers._sp:04X} (should be 0xDFEF)")

    assert cpu.registers._pc == 0x0302, f"PC should be 0x0302, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDFEF, f"SP should be 0xDFEF, got 0x{cpu.registers._sp:04X}"
    print("  PASS: PC correctly incremented by 2")

    # Test 4: Chained execution - multiple ADD SP,e in sequence
    print("\nTest 4: Chained ADD SP,e instructions")
    cpu.memory.write_byte(0x0400, 0xE8)  # ADD SP,$01
    cpu.memory.write_byte(0x0401, 0x01)
    cpu.memory.write_byte(0x0402, 0xE8)  # ADD SP,$02
    cpu.memory.write_byte(0x0403, 0x02)
    cpu.memory.write_byte(0x0404, 0xE8)  # ADD SP,$03
    cpu.memory.write_byte(0x0405, 0x03)
    cpu.memory.write_byte(0x0406, 0x00)  # NOP

    cpu.registers._pc = 0x0400
    cpu.registers._sp = 0xDF00

    print(f"  Starting: PC=0x{cpu.registers._pc:04X}, SP=0x{cpu.registers._sp:04X}")

    cpu.step()  # First ADD SP,$01
    print(f"  After 1st: PC=0x{cpu.registers._pc:04X} (should be 0x0402), SP=0x{cpu.registers._sp:04X} (should be 0xDF01)")
    assert cpu.registers._pc == 0x0402, f"PC should be 0x0402 after 1st, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDF01

    cpu.step()  # Second ADD SP,$02
    print(f"  After 2nd: PC=0x{cpu.registers._pc:04X} (should be 0x0404), SP=0x{cpu.registers._sp:04X} (should be 0xDF03)")
    assert cpu.registers._pc == 0x0404, f"PC should be 0x0404 after 2nd, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDF03

    cpu.step()  # Third ADD SP,$03
    print(f"  After 3rd: PC=0x{cpu.registers._pc:04X} (should be 0x0406), SP=0x{cpu.registers._sp:04X} (should be 0xDF06)")
    assert cpu.registers._pc == 0x0406, f"PC should be 0x0406 after 3rd, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDF06

    print("  PASS: Chained execution works correctly")

    # Test 5: Execute in RAM (like test 03 does)
    print("\nTest 5: ADD SP,e executed from RAM at 0xDEF8")
    cpu.memory.write_byte(0xDEF8, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0xDEF9, 0x05)  # e = +5
    cpu.memory.write_byte(0xDEFA, 0x00)  # NOP

    cpu.registers._pc = 0xDEF8
    cpu.registers._sp = 0xDF00

    print(f"  Before: PC=0x{cpu.registers._pc:04X}")
    cpu.step()
    print(f"  After:  PC=0x{cpu.registers._pc:04X} (should be 0xDEFA)")

    assert cpu.registers._pc == 0xDEFA, f"PC should be 0xDEFA, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDF05
    print("  PASS: Execution from RAM works correctly")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("PC is correctly incremented by 2 for ADD SP,e and LD HL,SP+e")
    print("=" * 80)

if __name__ == "__main__":
    test_pc_increment()
