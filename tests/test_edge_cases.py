"""
Edge case tests for Game Boy instructions

Tests unusual cases and memory operations that might cause issues
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

class EdgeCaseTester:
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

    def test_memory_indirect_operations(self):
        """Test operations using (HL) addressing"""
        print("\n=== Testing Memory Indirect Operations ===")

        # LD A,(HL) from RAM
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC050
        cpu.memory.write_byte(0xC050, 0x42)
        cpu.memory.write_byte(0x0000, 0x7E)  # LD A,(HL)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x42, "LD A,(HL) from RAM")

        # LD (HL),r to RAM
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC060
        cpu.registers._b = 0x99
        cpu.memory.write_byte(0x0000, 0x70)  # LD (HL),B
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC060), 0x99, "LD (HL),B to RAM")

        # INC (HL)
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC070
        cpu.memory.write_byte(0xC070, 0xFF)
        cpu.memory.write_byte(0x0000, 0x34)  # INC (HL)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC070), 0x00, "INC (HL) overflow")
        self.assert_equal(cpu.registers.flags.zero, True, "INC (HL) zero flag")

        # DEC (HL)
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC080
        cpu.memory.write_byte(0xC080, 0x01)
        cpu.memory.write_byte(0x0000, 0x35)  # DEC (HL)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC080), 0x00, "DEC (HL)")
        self.assert_equal(cpu.registers.flags.zero, True, "DEC (HL) zero flag")

    def test_ldi_ldd_instructions(self):
        """Test LDI and LDD instructions (load with increment/decrement)"""
        print("\n=== Testing LDI/LDD Instructions ===")

        # LDI (HL),A - load A to (HL) then increment HL
        cpu = self.setup_cpu()
        cpu.registers._a = 0x56
        cpu.registers.hl = 0xC000
        cpu.memory.write_byte(0x0000, 0x22)  # LDI (HL),A (or LD (HL+),A)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC000), 0x56, "LDI (HL),A stores value")
        self.assert_equal(cpu.registers.hl, 0xC001, "LDI (HL),A increments HL")

        # LDI A,(HL) - load (HL) to A then increment HL
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC010
        cpu.memory.write_byte(0xC010, 0x78)
        cpu.memory.write_byte(0x0000, 0x2A)  # LDI A,(HL) (or LD A,(HL+))
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x78, "LDI A,(HL) loads value")
        self.assert_equal(cpu.registers.hl, 0xC011, "LDI A,(HL) increments HL")

        # LDD (HL),A - load A to (HL) then decrement HL
        cpu = self.setup_cpu()
        cpu.registers._a = 0xAB
        cpu.registers.hl = 0xC020
        cpu.memory.write_byte(0x0000, 0x32)  # LDD (HL),A (or LD (HL-),A)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xC020), 0xAB, "LDD (HL),A stores value")
        self.assert_equal(cpu.registers.hl, 0xC01F, "LDD (HL),A decrements HL")

        # LDD A,(HL) - load (HL) to A then decrement HL
        cpu = self.setup_cpu()
        cpu.registers.hl = 0xC030
        cpu.memory.write_byte(0xC030, 0xCD)
        cpu.memory.write_byte(0x0000, 0x3A)  # LDD A,(HL) (or LD A,(HL-))
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0xCD, "LDD A,(HL) loads value")
        self.assert_equal(cpu.registers.hl, 0xC02F, "LDD A,(HL) decrements HL")

    def test_ldh_instructions(self):
        """Test LDH (0xFF00+n) instructions"""
        print("\n=== Testing LDH Instructions ===")

        # LDH (n),A - store A at 0xFF00+n
        cpu = self.setup_cpu()
        cpu.registers._a = 0x3C
        cpu.memory.write_byte(0x0000, 0xE0)  # LDH (n),A
        cpu.memory.write_byte(0x0001, 0x80)  # n = 0x80
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xFF80), 0x3C, "LDH (0x80),A")
        self.assert_equal(cpu.registers._pc, 0x0002, "LDH (n),A PC increment")

        # LDH A,(n) - load A from 0xFF00+n
        cpu = self.setup_cpu()
        cpu.memory.write_byte(0xFF90, 0x5A)
        cpu.memory.write_byte(0x0000, 0xF0)  # LDH A,(n)
        cpu.memory.write_byte(0x0001, 0x90)  # n = 0x90
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x5A, "LDH A,(0x90)")
        self.assert_equal(cpu.registers._pc, 0x0002, "LDH A,(n) PC increment")

        # LDH (C),A - store A at 0xFF00+C
        cpu = self.setup_cpu()
        cpu.registers._a = 0x12
        cpu.registers._c = 0x44
        cpu.memory.write_byte(0x0000, 0xE2)  # LDH (C),A
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.memory.read_byte(0xFF44), 0x12, "LDH (C),A")

        # LDH A,(C) - load A from 0xFF00+C
        cpu = self.setup_cpu()
        cpu.registers._c = 0x42
        cpu.memory.write_byte(0xFF42, 0x88)
        cpu.memory.write_byte(0x0000, 0xF2)  # LDH A,(C)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x88, "LDH A,(C)")

    def test_16bit_memory_loads(self):
        """Test 16-bit memory load operations"""
        print("\n=== Testing 16-bit Memory Loads ===")

        # LD (nn),SP - store SP at address nn
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFF8
        cpu.memory.write_byte(0x0000, 0x08)  # LD (nn),SP
        cpu.memory.write_byte(0x0001, 0x00)  # Low byte of address
        cpu.memory.write_byte(0x0002, 0xC1)  # High byte of address (0xC100)
        cpu.registers._pc = 0x0000
        cpu.step()
        low = cpu.memory.read_byte(0xC100)
        high = cpu.memory.read_byte(0xC101)
        sp_stored = low | (high << 8)
        self.assert_equal(sp_stored, 0xFFF8, "LD (0xC100),SP")
        self.assert_equal(cpu.registers._pc, 0x0003, "LD (nn),SP PC increment")

    def test_cp_instruction(self):
        """Test CP (compare) instruction"""
        print("\n=== Testing CP Instruction ===")

        # CP n (equal)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x3C
        cpu.memory.write_byte(0x0000, 0xFE)  # CP n
        cpu.memory.write_byte(0x0001, 0x3C)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.zero, True, "CP equal sets zero")
        self.assert_equal(cpu.registers.flags.carry, False, "CP equal no carry")
        self.assert_equal(cpu.registers._a, 0x3C, "CP doesn't modify A")

        # CP n (less than)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x02
        cpu.memory.write_byte(0x0000, 0xFE)  # CP n
        cpu.memory.write_byte(0x0001, 0x05)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.zero, False, "CP less than no zero")
        self.assert_equal(cpu.registers.flags.carry, True, "CP less than sets carry")

        # CP n (greater than)
        cpu = self.setup_cpu()
        cpu.registers._a = 0x10
        cpu.memory.write_byte(0x0000, 0xFE)  # CP n
        cpu.memory.write_byte(0x0001, 0x05)
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.zero, False, "CP greater than no zero")
        self.assert_equal(cpu.registers.flags.carry, False, "CP greater than no carry")

    def test_daa_instruction(self):
        """Test DAA (Decimal Adjust Accumulator)"""
        print("\n=== Testing DAA Instruction ===")

        # DAA after addition
        cpu = self.setup_cpu()
        cpu.registers._a = 0x45
        cpu.registers.flags.subtract = False
        cpu.registers.flags.half_carry = False
        cpu.registers.flags.carry = False
        # 0x45 + 0x38 in BCD = 45 + 38 = 83, so after ADD we'd have 0x7D
        # Then DAA should adjust to 0x83
        cpu.registers._a = 0x7D  # Simulate result of 0x45 + 0x38
        cpu.memory.write_byte(0x0000, 0x27)  # DAA
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0x83, "DAA after addition")

    def test_cpl_instruction(self):
        """Test CPL (complement A)"""
        print("\n=== Testing CPL Instruction ===")

        cpu = self.setup_cpu()
        cpu.registers._a = 0x35
        cpu.memory.write_byte(0x0000, 0x2F)  # CPL
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers._a, 0xCA, "CPL complements A")
        self.assert_equal(cpu.registers.flags.subtract, True, "CPL sets subtract")
        self.assert_equal(cpu.registers.flags.half_carry, True, "CPL sets half-carry")

    def test_scf_ccf_instructions(self):
        """Test SCF and CCF (Set/Complement Carry Flag)"""
        print("\n=== Testing SCF/CCF Instructions ===")

        # SCF - Set Carry Flag
        cpu = self.setup_cpu()
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0x37)  # SCF
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.carry, True, "SCF sets carry")
        self.assert_equal(cpu.registers.flags.subtract, False, "SCF clears subtract")
        self.assert_equal(cpu.registers.flags.half_carry, False, "SCF clears half-carry")

        # CCF - Complement Carry Flag
        cpu = self.setup_cpu()
        cpu.registers.flags.carry = True
        cpu.memory.write_byte(0x0000, 0x3F)  # CCF
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.carry, False, "CCF complements carry (true->false)")

        cpu = self.setup_cpu()
        cpu.registers.flags.carry = False
        cpu.memory.write_byte(0x0000, 0x3F)  # CCF
        cpu.registers._pc = 0x0000
        cpu.step()
        self.assert_equal(cpu.registers.flags.carry, True, "CCF complements carry (false->true)")

    def test_rst_instructions(self):
        """Test RST (restart) instructions"""
        print("\n=== Testing RST Instructions ===")

        # RST 0x00
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFFE
        cpu.registers._pc = 0x1234
        cpu.memory.write_byte(0x1234, 0xC7)  # RST 0x00
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0000, "RST 0x00 jumps to 0x0000")
        self.assert_equal(cpu.registers._sp, 0xFFFC, "RST decrements SP")
        ret_addr = cpu.memory.read_byte(0xFFFC) | (cpu.memory.read_byte(0xFFFD) << 8)
        self.assert_equal(ret_addr, 0x1235, "RST pushes return address")

        # RST 0x38
        cpu = self.setup_cpu()
        cpu.registers._sp = 0xFFFE
        cpu.registers._pc = 0x2000
        cpu.memory.write_byte(0x2000, 0xFF)  # RST 0x38
        cpu.step()
        self.assert_equal(cpu.registers._pc, 0x0038, "RST 0x38 jumps to 0x0038")

    def run_all_tests(self):
        """Run all edge case tests"""
        print("=" * 80)
        print("EDGE CASE INSTRUCTION TEST SUITE")
        print("=" * 80)

        self.test_memory_indirect_operations()
        self.test_ldi_ldd_instructions()
        self.test_ldh_instructions()
        self.test_16bit_memory_loads()
        self.test_cp_instruction()
        self.test_daa_instruction()
        self.test_cpl_instruction()
        self.test_scf_ccf_instructions()
        self.test_rst_instructions()

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
            print("\nPASS: ALL EDGE CASE TESTS PASSED!")
            print("=" * 80)
            return True

if __name__ == "__main__":
    tester = EdgeCaseTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
