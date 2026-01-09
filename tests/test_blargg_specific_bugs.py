"""
Test specific bug scenarios that could cause Blargg test 03 to fail

Based on common pitfalls in Game Boy emulator development:
1. XOR flag handling in CRC chains
2. SP arithmetic with signed values and flag edge cases
3. Rotation/shift flag handling in chains
4. Self-modifying code execution
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

class BlarggBugTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def assert_equal(self, actual, expected, message):
        """Assert that actual equals expected"""
        self.tests_run += 1
        if actual == expected:
            self.tests_passed += 1
            return True
        else:
            self.tests_failed += 1
            if isinstance(actual, bool) and isinstance(expected, bool):
                self.failures.append(f"{message}: expected {expected}, got {actual}")
            else:
                self.failures.append(f"{message}: expected 0x{expected:04X}, got 0x{actual:04X}")
            return False

    def setup_cpu(self):
        """Create a fresh CPU instance"""
        return CPU()

    def test_xor_flag_handling(self):
        """Test XOR flag handling - critical for CRC routines"""
        print("\n=== Testing XOR Flag Handling (CRC Critical) ===")

        # XOR A,A should set Z, clear N/H/C
        cpu = self.setup_cpu()
        cpu.registers._a = 0xFF
        cpu.registers.flags.carry = True
        cpu.registers.flags.half_carry = True
        cpu.registers.flags.subtract = True
        cpu.memory.write_byte(0x0000, 0xAF)  # XOR A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "XOR A,A result")
        self.assert_equal(cpu.registers.flags.zero, True, "XOR A,A zero flag")
        self.assert_equal(cpu.registers.flags.subtract, False, "XOR A,A subtract flag MUST be 0")
        self.assert_equal(cpu.registers.flags.half_carry, False, "XOR A,A half-carry MUST be 0")
        self.assert_equal(cpu.registers.flags.carry, False, "XOR A,A carry MUST be 0")

        # XOR n with non-zero result
        cpu = self.setup_cpu()
        cpu.registers._a = 0xAA
        cpu.registers.flags.carry = True
        cpu.registers.flags.half_carry = True
        cpu.memory.write_byte(0x0000, 0xEE)  # XOR n
        cpu.memory.write_byte(0x0001, 0x55)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0xFF, "XOR 0x55 result")
        self.assert_equal(cpu.registers.flags.zero, False, "XOR non-zero zero flag")
        self.assert_equal(cpu.registers.flags.carry, False, "XOR carry MUST be 0")
        self.assert_equal(cpu.registers.flags.half_carry, False, "XOR half-carry MUST be 0")

        # XOR in a chain (simulating CRC)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x12
        cpu.registers._b = 0x34

        # XOR A,B
        cpu.memory.write_byte(0x0000, 0xA8)  # XOR B
        cpu.registers._pc = 0x0000
        cpu.step()

        result1 = cpu.registers._a  # Should be 0x12 ^ 0x34 = 0x26
        self.assert_equal(result1, 0x26, "XOR chain step 1")
        self.assert_equal(cpu.registers.flags.carry, False, "XOR chain carry clear")

        # XOR A,n again
        cpu.memory.write_byte(0x0001, 0xEE)  # XOR n
        cpu.memory.write_byte(0x0002, 0x26)
        cpu.step()

        self.assert_equal(cpu.registers._a, 0x00, "XOR chain final (CRC pattern)")
        self.assert_equal(cpu.registers.flags.zero, True, "XOR chain zero")
        self.assert_equal(cpu.registers.flags.carry, False, "XOR chain carry still clear")

    def test_and_or_flag_handling(self):
        """Test AND/OR flag handling - also used in CRC"""
        print("\n=== Testing AND/OR Flag Handling ===")

        # AND should set H=1, clear N and C
        cpu = self.setup_cpu()
        cpu.registers._a = 0xFF
        cpu.registers.flags.carry = True
        cpu.registers.flags.subtract = True
        cpu.memory.write_byte(0x0000, 0xE6)  # AND n
        cpu.memory.write_byte(0x0001, 0x00)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "AND 0x00 result")
        self.assert_equal(cpu.registers.flags.zero, True, "AND zero flag")
        self.assert_equal(cpu.registers.flags.half_carry, True, "AND half-carry MUST be 1")
        self.assert_equal(cpu.registers.flags.subtract, False, "AND subtract MUST be 0")
        self.assert_equal(cpu.registers.flags.carry, False, "AND carry MUST be 0")

        # OR should clear N, H, C
        cpu = self.setup_cpu()
        cpu.registers._a = 0x00
        cpu.registers.flags.carry = True
        cpu.registers.flags.half_carry = True
        cpu.registers.flags.subtract = True
        cpu.memory.write_byte(0x0000, 0xF6)  # OR n
        cpu.memory.write_byte(0x0001, 0xFF)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0xFF, "OR 0xFF result")
        self.assert_equal(cpu.registers.flags.zero, False, "OR zero flag")
        self.assert_equal(cpu.registers.flags.half_carry, False, "OR half-carry MUST be 0")
        self.assert_equal(cpu.registers.flags.subtract, False, "OR subtract MUST be 0")
        self.assert_equal(cpu.registers.flags.carry, False, "OR carry MUST be 0")

    def test_sp_signed_arithmetic_edge_cases(self):
        """Test ADD SP,e and LD HL,SP+e with signed edge cases"""
        print("\n=== Testing SP Signed Arithmetic Edge Cases ===")

        # ADD SP,e: positive offset with half-carry
        cpu = self.setup_cpu()
        cpu.registers._sp = 0x00F8  # Low byte = 0xF8
        cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
        cpu.memory.write_byte(0x0001, 0x08)  # e = +8
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0x0100, "ADD SP,+8 result")
        # Flags based on LOW BYTE only: 0xF8 + 0x08 = 0x100
        # Half-carry: (0xF8 & 0xF) + (0x08 & 0xF) = 0x8 + 0x8 = 0x10, so H=1
        # Carry: (0xF8 & 0xFF) + (0x08 & 0xFF) = 0xF8 + 0x08 = 0x100, so C=1
        self.assert_equal(cpu.registers.flags.half_carry, True, "ADD SP,+8 half-carry")
        self.assert_equal(cpu.registers.flags.carry, True, "ADD SP,+8 carry")
        self.assert_equal(cpu.registers.flags.zero, False, "ADD SP zero MUST be 0")
        self.assert_equal(cpu.registers.flags.subtract, False, "ADD SP subtract MUST be 0")

        # ADD SP,e: negative offset
        cpu = self.setup_cpu()
        cpu.registers._sp = 0x0002
        cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
        cpu.memory.write_byte(0x0001, 0xFF)  # e = -1 (0xFF as signed byte)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0x0001, "ADD SP,-1 result")
        # Flags: LOW BYTE calc: 0x02 + 0xFF = 0x101
        # H: (0x02 & 0xF) + (0xFF & 0xF) = 0x2 + 0xF = 0x11, so H=1
        # C: (0x02 & 0xFF) + (0xFF & 0xFF) = 0x02 + 0xFF = 0x101, so C=1
        self.assert_equal(cpu.registers.flags.half_carry, True, "ADD SP,-1 half-carry")
        self.assert_equal(cpu.registers.flags.carry, True, "ADD SP,-1 carry")

        # ADD SP,e: edge case SP=0xFFFF + 1
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFFF
        cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,e
        cpu.memory.write_byte(0x0001, 0x01)  # e = +1
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0x0000, "ADD SP,+1 wrap result")
        # LOW BYTE: 0xFF + 0x01 = 0x100
        # H: (0xFF & 0xF) + (0x01 & 0xF) = 0xF + 0x1 = 0x10, so H=1
        # C: (0xFF & 0xFF) + (0x01 & 0xFF) = 0xFF + 0x01 = 0x100, so C=1
        self.assert_equal(cpu.registers.flags.half_carry, True, "ADD SP wrap half-carry")
        self.assert_equal(cpu.registers.flags.carry, True, "ADD SP wrap carry")

        # LD HL,SP+e: same flag behavior, but doesn't modify SP
        cpu = self.setup_cpu()
        cpu.registers._sp = 0x00F8
        cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
        cpu.memory.write_byte(0x0001, 0x08)  # e = +8
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.hl, 0x0100, "LD HL,SP+8 result")
        self.assert_equal(cpu.registers._sp, 0x00F8, "LD HL,SP+e doesn't change SP")
        self.assert_equal(cpu.registers.flags.half_carry, True, "LD HL,SP+8 half-carry")
        self.assert_equal(cpu.registers.flags.carry, True, "LD HL,SP+8 carry")
        self.assert_equal(cpu.registers.flags.zero, False, "LD HL,SP zero MUST be 0")
        self.assert_equal(cpu.registers.flags.subtract, False, "LD HL,SP subtract MUST be 0")

        # LD HL,SP+e: negative offset with no carry
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFF00
        cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+e
        cpu.memory.write_byte(0x0001, 0x10)  # e = +16
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.hl, 0xFF10, "LD HL,SP+16 result")
        # LOW BYTE: 0x00 + 0x10 = 0x10
        # H: (0x00 & 0xF) + (0x10 & 0xF) = 0x0 + 0x0 = 0x0, so H=0
        # C: (0x00 & 0xFF) + (0x10 & 0xFF) = 0x00 + 0x10 = 0x10, so C=0
        self.assert_equal(cpu.registers.flags.half_carry, False, "LD HL,SP+16 no half-carry")
        self.assert_equal(cpu.registers.flags.carry, False, "LD HL,SP+16 no carry")

    def test_rotation_shift_flag_chains(self):
        """Test rotation/shift instructions in chains (CRC usage)"""
        print("\n=== Testing Rotation/Shift Flag Chains ===")

        # RR A (rotate right through carry)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x01
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x1F)  # RR A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "RR A value (bit 0 -> carry)")
        self.assert_equal(cpu.registers.flags.carry, True, "RR A carry (old bit 0)")
        self.assert_equal(cpu.registers.flags.zero, True, "RR A zero flag")
        self.assert_equal(cpu.registers.flags.subtract, False, "RR A subtract MUST be 0")
        self.assert_equal(cpu.registers.flags.half_carry, False, "RR A half-carry MUST be 0")

        # RR A with carry in
        cpu = self.setup_cpu()
        cpu.registers._a = 0x8A
        cpu.registers.flags.carry = True
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x1F)  # RR A
        cpu.registers._pc = 0x0000
        cpu.step()
        # Result: carry goes to bit 7, bit 0 goes to carry
        # 0x8A = 10001010, bit 0 = 0, carry was 1
        # Result = 11000101 = 0xC5
        self.assert_equal(cpu.registers._a, 0xC5, "RR A with carry in")
        self.assert_equal(cpu.registers.flags.carry, False, "RR A carry out (old bit 0)")

        # RL A (rotate left through carry)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x80
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x17)  # RL A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "RL A value (bit 7 -> carry)")
        self.assert_equal(cpu.registers.flags.carry, True, "RL A carry (old bit 7)")
        self.assert_equal(cpu.registers.flags.zero, True, "RL A zero flag")

        # Chain: RR then RR again
        cpu = self.setup_cpu()
        cpu.registers._a = 0x03
        cpu.registers.flags.carry = False

        # First RR
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x1F)  # RR A
        cpu.registers._pc = 0x0000
        cpu.step()

        first_result = cpu.registers._a  # 0x03 >> 1 = 0x01
        first_carry = cpu.registers.flags.carry  # bit 0 of 0x03 = 1
        self.assert_equal(first_result, 0x01, "RR chain first step")
        self.assert_equal(first_carry, True, "RR chain first carry")

        # Second RR
        cpu.memory.write_byte(0x0002, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0003, 0x1F)  # RR A
        cpu.step()

        # 0x01 with carry=1 in -> 10000000 = 0x80
        self.assert_equal(cpu.registers._a, 0x80, "RR chain second step")
        self.assert_equal(cpu.registers.flags.carry, True, "RR chain second carry (bit 0 of 0x01)")

    def test_self_modifying_code(self):
        """Test execution of self-modifying code"""
        print("\n=== Testing Self-Modifying Code ===")

        cpu = self.setup_cpu()

        # Write initial code to RAM at 0xC000
        cpu.memory.write_byte(0xC000, 0x00)  # NOP initially
        cpu.memory.write_byte(0xC001, 0xC9)  # RET

        # Execute code that modifies 0xC000 then jumps there
        cpu.memory.write_byte(0x0000, 0x3E)  # LD A,0x3C
        cpu.memory.write_byte(0x0001, 0x3C)
        cpu.memory.write_byte(0x0002, 0xEA)  # LD (nn),A
        cpu.memory.write_byte(0x0003, 0x00)  # Low byte of 0xC000
        cpu.memory.write_byte(0x0004, 0xC0)  # High byte
        cpu.memory.write_byte(0x0005, 0xC3)  # JP 0xC000
        cpu.memory.write_byte(0x0006, 0x00)
        cpu.memory.write_byte(0x0007, 0xC0)

        cpu.registers._pc = 0x0000
        cpu.registers._sp = 0xFFFE

        # Execute: LD A,0x3C
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x3C, "Self-mod: load value")

        # Execute: LD (0xC000),A (modify the code)
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC000), 0x3C, "Self-mod: write to RAM")

        # Execute: JP 0xC000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0xC000, "Self-mod: jump to RAM")

        # Now execute the MODIFIED code (should be 0x3C = INC A, not NOP)
        a_before = cpu.registers._a
        cpu.step()

        # If self-modifying code works, we executed 0x3C (INC A), so A should increment
        # If it doesn't work, we executed NOP, so A stays the same
        self.assert_equal(cpu.registers._a, a_before + 1, "Self-mod: executed modified code (INC A)")
        self.assert_equal(cpu.registers._pc, 0xC001, "Self-mod: PC advanced")

    def run_all_tests(self):
        """Run all Blargg-specific bug tests"""
        print("=" * 80)
        print("BLARGG TEST 03 SPECIFIC BUG TESTS")
        print("=" * 80)

        self.test_xor_flag_handling()
        self.test_and_or_flag_handling()
        self.test_sp_signed_arithmetic_edge_cases()
        self.test_rotation_shift_flag_chains()
        self.test_self_modifying_code()

        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print(f"Tests Run:    {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print("=" * 80)

        if self.tests_failed > 0:
            print("\nFAILURES:")
            for failure in self.failures:
                print(f"  FAIL: {failure}")
            print("=" * 80)
            return False
        else:
            print("\nPASS: ALL BLARGG-SPECIFIC TESTS PASSED!")
            print("=" * 80)
            return True

if __name__ == "__main__":
    tester = BlarggBugTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
