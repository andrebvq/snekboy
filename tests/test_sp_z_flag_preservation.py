"""
Test that ADD SP,e and LD HL,SP+e preserve the Z flag
This is the bug that was causing Blargg test 03 to fail!
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_z_preservation():
    cpu = CPU()

    print("Testing Z flag preservation in ADD SP,e and LD HL,SP+e")
    print("=" * 80)

    # Test 1: ADD SP,0 with Z=0
    print("\nTest 1: ADD SP,0 with Z=0 (should stay Z=0)")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0x00)  # e=0
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = False
    cpu.step()
    assert cpu.registers.flags.zero == False, "Z should remain 0"
    print("  PASS: Z remained 0")

    # Test 2: ADD SP,0 with Z=1
    print("\nTest 2: ADD SP,0 with Z=1 (should stay Z=1)")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0x00)  # e=0
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = True
    cpu.step()
    assert cpu.registers.flags.zero == True, "Z should remain 1"
    print("  PASS: Z remained 1")

    # Test 3: ADD SP,5 with Z=0
    print("\nTest 3: ADD SP,5 with Z=0 (should stay Z=0)")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0x05)  # e=5
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = False
    cpu.step()
    assert cpu.registers._sp == 0xDFF5, f"SP should be 0xDFF5, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == False, "Z should remain 0"
    print("  PASS: Z remained 0, SP correctly updated")

    # Test 4: ADD SP,5 with Z=1
    print("\nTest 4: ADD SP,5 with Z=1 (should stay Z=1)")
    cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
    cpu.memory.write_byte(0x0001, 0x05)  # e=5
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = True
    cpu.step()
    assert cpu.registers._sp == 0xDFF5, f"SP should be 0xDFF5, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers.flags.zero == True, "Z should remain 1"
    print("  PASS: Z remained 1, SP correctly updated")

    # Test 5: LD HL,SP+0 with Z=0
    print("\nTest 5: LD HL,SP+0 with Z=0 (should stay Z=0)")
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
    cpu.memory.write_byte(0x0001, 0x00)  # e=0
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = False
    cpu.step()
    assert cpu.registers.hl == 0xDFF0, f"HL should be 0xDFF0, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == False, "Z should remain 0"
    print("  PASS: Z remained 0, HL correctly loaded")

    # Test 6: LD HL,SP+0 with Z=1
    print("\nTest 6: LD HL,SP+0 with Z=1 (should stay Z=1)")
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
    cpu.memory.write_byte(0x0001, 0x00)  # e=0
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = True
    cpu.step()
    assert cpu.registers.hl == 0xDFF0, f"HL should be 0xDFF0, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == True, "Z should remain 1"
    print("  PASS: Z remained 1, HL correctly loaded")

    # Test 7: LD HL,SP+5 with Z=1
    print("\nTest 7: LD HL,SP+5 with Z=1 (should stay Z=1)")
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
    cpu.memory.write_byte(0x0001, 0x05)  # e=5
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = True
    cpu.step()
    assert cpu.registers.hl == 0xDFF5, f"HL should be 0xDFF5, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == True, "Z should remain 1"
    print("  PASS: Z remained 1, HL correctly loaded")

    # Test 8: LD HL,SP+(-5) with Z=0
    print("\nTest 8: LD HL,SP+(-5) with Z=0 (should stay Z=0)")
    cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
    cpu.memory.write_byte(0x0001, 0xFB)  # e=-5 (two's complement)
    cpu.registers._pc = 0x0000
    cpu.registers._sp = 0xDFF0
    cpu.registers.flags.zero = False
    cpu.step()
    assert cpu.registers.hl == 0xDFEB, f"HL should be 0xDFEB, got 0x{cpu.registers.hl:04X}"
    assert cpu.registers.flags.zero == False, "Z should remain 0"
    print("  PASS: Z remained 0, HL correctly loaded with negative offset")

    print()
    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("Z flag is now correctly preserved in ADD SP,e and LD HL,SP+e")
    print("=" * 80)

if __name__ == "__main__":
    test_z_preservation()
