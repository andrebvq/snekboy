from cpu import CPU, Instruction, InstructionType, ArithmeticTarget

def test_flags():
    cpu = CPU()
    
    # Test flag operations
    print("Initial flags:", cpu.registers.flags)
    
    # Set some flags
    cpu.registers.flags.zero = True
    cpu.registers.flags.carry = True
    print("After setting Z and C:", cpu.registers.flags)
    
    # Clear a flag
    cpu.registers.flags.zero = False
    print("After clearing Z:", cpu.registers.flags)
    
    # Test flag byte conversion
    flag_byte = cpu.registers.flags.to_byte()
    print(f"Flags as byte: 0x{flag_byte:02X}")
    
    # Set flags from byte
    cpu.registers.flags.from_byte(0b11110000)
    print("After setting from byte:", cpu.registers.flags)

def test_add_instruction():
    """Test ADD instruction execution"""
    cpu = CPU()
    print("Initial CPU state:")
    print(cpu)
    
    instruction = Instruction(InstructionType.ADD, ArithmeticTarget.B)
    cpu.execute(instruction)
    print("\nAfter ADD B:")
    print(cpu)

def run_all_tests():
    print("=== Testing Flags ===")
    test_flags()
    print("\n=== Testing ADD Instruction ===")
    test_add_instruction()