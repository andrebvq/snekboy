"""
Comprehensive test suite for ALL Game Boy instructions

Tests each instruction against known expected behavior from official documentation.
This will help identify which instruction(s) are causing test 03 to fail.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

class InstructionTester:
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
            self.failures.append(f"{message}: expected 0x{expected:04X}, got 0x{actual:04X}")
            return False

    def setup_cpu(self):
        """Create a fresh CPU instance"""
        return CPU()

    def test_8bit_loads(self):
        """Test 8-bit load instructions"""
        print("\n=== Testing 8-bit Load Instructions ===")

        # LD r,n (load immediate to register)
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0x0000, 0x3E)  # LD A,n
        cpu.memory.write_byte(0x0001, 0x42)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x42, "LD A,0x42")
        self.assert_equal(cpu.registers._pc, 0x0002, "LD A,n PC increment")

        # LD r,r (register to register)
        cpu = self.setup_cpu()
        cpu.registers._b = 0x55
        cpu.memory.write_byte(0x0000, 0x78)  # LD A,B
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x55, "LD A,B")
        self.assert_equal(cpu.registers._pc, 0x0001, "LD A,B PC increment")

        # LD (HL),n
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC000
        cpu.memory.write_byte(0x0000, 0x36)  # LD (HL),n
        cpu.memory.write_byte(0x0001, 0x99)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC000), 0x99, "LD (HL),0x99")
        self.assert_equal(cpu.registers._pc, 0x0002, "LD (HL),n PC increment")

    def test_16bit_loads(self):
        """Test 16-bit load instructions"""
        print("\n=== Testing 16-bit Load Instructions ===")

        # LD BC,nn
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0x0000, 0x01)  # LD BC,nn
        cpu.memory.write_byte(0x0001, 0x34)  # Low byte
        cpu.memory.write_byte(0x0002, 0x12)  # High byte
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.bc, 0x1234, "LD BC,0x1234")
        self.assert_equal(cpu.registers._pc, 0x0003, "LD BC,nn PC increment")

        # LD SP,HL
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xFFF8
        cpu.memory.write_byte(0x0000, 0xF9)  # LD SP,HL
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0xFFF8, "LD SP,HL")
        self.assert_equal(cpu.registers._pc, 0x0001, "LD SP,HL PC increment")

    def test_stack_operations(self):
        """Test PUSH and POP instructions"""
        print("\n=== Testing Stack Operations ===")

        # PUSH BC
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFFE
        cpu.registers.bc = 0x1234
        cpu.memory.write_byte(0x0000, 0xC5)  # PUSH BC
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0xFFFC, "PUSH BC SP decrement")
        self.assert_equal(cpu.memory.read_byte(0xFFFC), 0x34, "PUSH BC low byte")
        self.assert_equal(cpu.memory.read_byte(0xFFFC + 1), 0x12, "PUSH BC high byte")
        self.assert_equal(cpu.registers._pc, 0x0001, "PUSH BC PC increment")

        # POP DE
        cpu.memory.write_byte(0x0001, 0xD1)  # POP DE
        cpu.step()
        self.assert_equal(cpu.registers.de, 0x1234, "POP DE value")
        self.assert_equal(cpu.registers._sp, 0xFFFE, "POP DE SP increment")
        self.assert_equal(cpu.registers._pc, 0x0002, "POP DE PC increment")

    def test_arithmetic_8bit(self):
        """Test 8-bit arithmetic instructions"""
        print("\n=== Testing 8-bit Arithmetic ===")

        # ADD A,n
        cpu = self.setup_cpu()
        cpu.registers._a = 0x3C
        cpu.memory.write_byte(0x0000, 0xC6)  # ADD A,n
        cpu.memory.write_byte(0x0001, 0x12)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x4E, "ADD A,0x12")
        self.assert_equal(cpu.registers.flags.zero, False, "ADD A,n zero flag")
        self.assert_equal(cpu.registers.flags.carry, False, "ADD A,n carry flag")
        self.assert_equal(cpu.registers._pc, 0x0002, "ADD A,n PC increment")

        # ADD A,n with carry
        cpu = self.setup_cpu()
        cpu.registers._a = 0xFF
        cpu.memory.write_byte(0x0000, 0xC6)  # ADD A,n
        cpu.memory.write_byte(0x0001, 0x01)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "ADD A,1 (overflow)")
        self.assert_equal(cpu.registers.flags.zero, True, "ADD overflow zero flag")
        self.assert_equal(cpu.registers.flags.carry, True, "ADD overflow carry flag")

        # SUB n
        cpu = self.setup_cpu()
        cpu.registers._a = 0x3E
        cpu.memory.write_byte(0x0000, 0xD6)  # SUB n
        cpu.memory.write_byte(0x0001, 0x0F)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x2F, "SUB 0x0F")
        self.assert_equal(cpu.registers.flags.subtract, True, "SUB subtract flag")
        self.assert_equal(cpu.registers.flags.carry, False, "SUB carry flag")

        # SUB n with borrow
        cpu = self.setup_cpu()
        cpu.registers._a = 0x05
        cpu.memory.write_byte(0x0000, 0xD6)  # SUB n
        cpu.memory.write_byte(0x0001, 0x0A)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0xFB, "SUB 0x0A (underflow)")
        self.assert_equal(cpu.registers.flags.carry, True, "SUB underflow carry flag")

        # INC r
        cpu = self.setup_cpu()
        cpu.registers._b = 0x0F
        cpu.memory.write_byte(0x0000, 0x04)  # INC B
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._b, 0x10, "INC B")
        self.assert_equal(cpu.registers.flags.half_carry, True, "INC B half-carry")
        self.assert_equal(cpu.registers._pc, 0x0001, "INC B PC increment")

        # DEC r
        cpu = self.setup_cpu()
        cpu.registers._c = 0x01
        cpu.memory.write_byte(0x0000, 0x0D)  # DEC C
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._c, 0x00, "DEC C")
        self.assert_equal(cpu.registers.flags.zero, True, "DEC C zero flag")
        self.assert_equal(cpu.registers.flags.subtract, True, "DEC C subtract flag")

    def test_arithmetic_16bit(self):
        """Test 16-bit arithmetic instructions"""
        print("\n=== Testing 16-bit Arithmetic ===")

        # ADD HL,BC
        cpu = self.setup_cpu()
        cpu.registers.hl = 0x8A23
        cpu.registers.bc = 0x0605
        cpu.memory.write_byte(0x0000, 0x09)  # ADD HL,BC
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.hl, 0x9028, "ADD HL,BC")
        self.assert_equal(cpu.registers.flags.subtract, False, "ADD HL,BC subtract flag")
        self.assert_equal(cpu.registers._pc, 0x0001, "ADD HL,BC PC increment")

        # INC BC
        cpu = self.setup_cpu()
        cpu.registers.bc = 0x235F
        cpu.memory.write_byte(0x0000, 0x03)  # INC BC
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.bc, 0x2360, "INC BC")
        self.assert_equal(cpu.registers._pc, 0x0001, "INC BC PC increment")

        # DEC DE
        cpu = self.setup_cpu()
        cpu.registers.de = 0x2360
        cpu.memory.write_byte(0x0000, 0x1B)  # DEC DE
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.de, 0x235F, "DEC DE")
        self.assert_equal(cpu.registers._pc, 0x0001, "DEC DE PC increment")

        # ADD SP,n (signed)
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFF8
        cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,n
        cpu.memory.write_byte(0x0001, 0x02)  # n = 2
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0xFFFA, "ADD SP,2")
        self.assert_equal(cpu.registers._pc, 0x0002, "ADD SP,n PC increment")

        # ADD SP,n (signed negative)
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFF8
        cpu.memory.write_byte(0x0000, 0xE8)  # ADD SP,n
        cpu.memory.write_byte(0x0001, 0xFF)  # n = -1 (0xFF as signed)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._sp, 0xFFF7, "ADD SP,-1")

        # LD HL,SP+n
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFF8
        cpu.memory.write_byte(0x0000, 0xF8)  # LD HL,SP+n
        cpu.memory.write_byte(0x0001, 0x02)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.hl, 0xFFFA, "LD HL,SP+2")
        self.assert_equal(cpu.registers._sp, 0xFFF8, "LD HL,SP+n doesn't change SP")
        self.assert_equal(cpu.registers._pc, 0x0002, "LD HL,SP+n PC increment")

    def test_logical_operations(self):
        """Test logical operations (AND, OR, XOR)"""
        print("\n=== Testing Logical Operations ===")

        # AND n
        cpu = self.setup_cpu()
        cpu.registers._a = 0x5A
        cpu.memory.write_byte(0x0000, 0xE6)  # AND n
        cpu.memory.write_byte(0x0001, 0x3F)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x1A, "AND 0x3F")
        self.assert_equal(cpu.registers.flags.half_carry, True, "AND half-carry flag")
        self.assert_equal(cpu.registers.flags.subtract, False, "AND subtract flag")
        self.assert_equal(cpu.registers.flags.carry, False, "AND carry flag")

        # OR n
        cpu = self.setup_cpu()
        cpu.registers._a = 0x5A
        cpu.memory.write_byte(0x0000, 0xF6)  # OR n
        cpu.memory.write_byte(0x0001, 0x03)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x5B, "OR 0x03")
        self.assert_equal(cpu.registers.flags.zero, False, "OR zero flag")

        # XOR n
        cpu = self.setup_cpu()
        cpu.registers._a = 0xFF
        cpu.memory.write_byte(0x0000, 0xEE)  # XOR n
        cpu.memory.write_byte(0x0001, 0xFF)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x00, "XOR 0xFF")
        self.assert_equal(cpu.registers.flags.zero, True, "XOR zero flag")

    def test_jumps_and_calls(self):
        """Test jump and call instructions"""
        print("\n=== Testing Jumps and Calls ===")

        # JP nn (unconditional)
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0x0000, 0xC3)  # JP nn
        cpu.memory.write_byte(0x0001, 0x50)
        cpu.memory.write_byte(0x0002, 0x01)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0150, "JP 0x0150")

        # JP NZ,nn (condition false - don't jump)
        cpu = self.setup_cpu()
        cpu.registers.flags.zero = True
        cpu.memory.write_byte(0x0000, 0xC2)  # JP NZ,nn
        cpu.memory.write_byte(0x0001, 0x50)
        cpu.memory.write_byte(0x0002, 0x01)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0003, "JP NZ (not taken)")

        # JP NZ,nn (condition true - jump)
        cpu = self.setup_cpu()
        cpu.registers.flags.zero = False
        cpu.memory.write_byte(0x0000, 0xC2)  # JP NZ,nn
        cpu.memory.write_byte(0x0001, 0x50)
        cpu.memory.write_byte(0x0002, 0x01)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0150, "JP NZ (taken)")

        # JR e (relative jump)
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0x0000, 0x18)  # JR e
        cpu.memory.write_byte(0x0001, 0x05)  # Jump forward 5
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0007, "JR +5")  # 0x0002 + 5 = 0x0007

        # JR e (negative offset)
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0x0100, 0x18)  # JR e
        cpu.memory.write_byte(0x0101, 0xFE)  # Jump back 2 (-2 as signed byte)
        cpu.registers._pc = 0x0100
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0100, "JR -2")  # 0x0102 + (-2) = 0x0100

        # CALL nn
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFFE
        cpu.memory.write_byte(0x0000, 0xCD)  # CALL nn
        cpu.memory.write_byte(0x0001, 0x34)
        cpu.memory.write_byte(0x0002, 0x12)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x1234, "CALL 0x1234 PC")
        self.assert_equal(cpu.registers._sp, 0xFFFC, "CALL SP decrement")
        # Return address should be 0x0003
        ret_addr = cpu.memory.read_byte(0xFFFC) | (cpu.memory.read_byte(0xFFFD) << 8)
        self.assert_equal(ret_addr, 0x0003, "CALL return address on stack")

        # RET
        cpu.memory.write_byte(0x1234, 0xC9)  # RET
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0003, "RET PC")
        self.assert_equal(cpu.registers._sp, 0xFFFE, "RET SP increment")

    def test_bit_operations(self):
        """Test bit manipulation instructions (CB prefix)"""
        print("\n=== Testing Bit Operations ===")

        # BIT 7,A
        cpu = self.setup_cpu()
        cpu.registers._a = 0x80
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x7F)  # BIT 7,A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.zero, False, "BIT 7,A (bit set)")
        self.assert_equal(cpu.registers._pc, 0x0002, "BIT PC increment")

        # SET 3,B
        cpu = self.setup_cpu()
        cpu.registers._b = 0x00
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0xD8)  # SET 3,B
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._b, 0x08, "SET 3,B")

        # RES 7,A
        cpu = self.setup_cpu()
        cpu.registers._a = 0xFF
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0xBF)  # RES 7,A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x7F, "RES 7,A")

        # RL A (rotate left through carry)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x85
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0xCB)  # CB prefix
        cpu.memory.write_byte(0x0001, 0x17)  # RL A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x0A, "RL A value")
        self.assert_equal(cpu.registers.flags.carry, True, "RL A carry out")

    def test_rotates_and_shifts(self):
        """Test rotate and shift instructions"""
        print("\n=== Testing Rotates and Shifts ===")

        # RLCA (rotate A left, no carry)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x85
        cpu.memory.write_byte(0x0000, 0x07)  # RLCA
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x0B, "RLCA value")
        self.assert_equal(cpu.registers.flags.carry, True, "RLCA carry")
        self.assert_equal(cpu.registers._pc, 0x0001, "RLCA PC increment")

        # RRA (rotate A right through carry)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x81
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0x1F)  # RRA
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x40, "RRA value")
        self.assert_equal(cpu.registers.flags.carry, True, "RRA carry")

    def run_all_tests(self):
        """Run all instruction tests"""
        print("=" * 80)
        print("COMPREHENSIVE INSTRUCTION TEST SUITE")
        print("=" * 80)

        self.test_8bit_loads()
        self.test_16bit_loads()
        self.test_stack_operations()
        self.test_arithmetic_8bit()
        self.test_arithmetic_16bit()
        self.test_logical_operations()
        self.test_jumps_and_calls()
        self.test_bit_operations()
        self.test_rotates_and_shifts()

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
            print("\nPASS: ALL TESTS PASSED!")
            print("=" * 80)
            return True

if __name__ == "__main__":
    tester = InstructionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
