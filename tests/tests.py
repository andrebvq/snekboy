from snekboy.src.cpu import CPU, Instruction, InstructionType, ArithmeticTarget

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
    # Test cases structure: (a_value, target_value, expected_result, expected_flags)
    # expected_flags is a tuple of (zero, subtract, half_carry, carry)
    test_cases = [
        # Basic addition
        (0x00, 0x01, 0x01, (False, False, False, False)),  # 0 + 1 = 1
        (0x01, 0x02, 0x03, (False, False, False, False)),  # 1 + 2 = 3
        
        # Zero flag tests
        (0xFF, 0x01, 0x00, (True, False, True, True)),    # 255 + 1 = 0 (with carry)
        (0x80, 0x80, 0x00, (True, False, False, True)),   # 128 + 128 = 0 (with carry)
        
        # Carry flag tests
        (0xFF, 0x02, 0x01, (False, False, True, True)),   # 255 + 2 = 1 (with carry)
        (0x80, 0x81, 0x01, (False, False, False, True)),  # 128 + 129 = 1 (with carry, but no half carry)
        
        # Half carry flag tests
        (0x0F, 0x01, 0x10, (False, False, True, False)),  # 15 + 1 = 16 (half carry)
        (0x1F, 0x01, 0x20, (False, False, True, False)),  # 31 + 1 = 32 (half carry)
        
        # Multiple flags combination
        (0xF0, 0x10, 0x00, (True, False, True, True)),    # 240 + 16 = 0 (zero, carry, half carry)
        
        # Edge cases
        (0x00, 0x00, 0x00, (True, False, False, False)),  # 0 + 0 = 0
        (0xFF, 0xFF, 0xFE, (False, False, True, True)),   # 255 + 255 = 254 (with carry)
    ]
    
    for a_value, target_value, expected_result, expected_flags in test_cases:
        cpu = CPU()
        
        # Set initial values
        cpu.registers._a = a_value
        cpu.registers._b = target_value  # We'll use register B for testing
        
        # Create and execute ADD instruction
        instruction = Instruction(type=InstructionType.ADD, target=ArithmeticTarget.B)
        cpu.execute(instruction)
        
        # Check result
        assert cpu.registers._a == expected_result, \
            f"Failed ADD {a_value:02X} + {target_value:02X}: expected {expected_result:02X}, got {cpu.registers._a:02X}"
        
        # Check flags
        expected_zero, expected_subtract, expected_half_carry, expected_carry = expected_flags
        assert cpu.registers.flags.zero == expected_zero, \
            f"Wrong zero flag for {a_value:02X} + {target_value:02X}"
        assert cpu.registers.flags.subtract == expected_subtract, \
            f"Wrong subtract flag for {a_value:02X} + {target_value:02X}"
        assert cpu.registers.flags.half_carry == expected_half_carry, \
            f"Wrong half carry flag for {a_value:02X} + {target_value:02X}"
        assert cpu.registers.flags.carry == expected_carry, \
            f"Wrong carry flag for {a_value:02X} + {target_value:02X}"
    
    print('ADD test complete')