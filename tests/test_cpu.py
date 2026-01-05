from src.cpu import CPU
from src.memory import Memory

def test_nop_instruction():
    """Test NOP (0x00) instruction"""
    mem = Memory()
    mem.write_byte(0x0100, 0x00)  # NOP at entry point
    
    cpu = CPU(mem)
    initial_pc = cpu.registers._pc
    
    cpu.step()
    
    assert cpu.registers._pc == initial_pc + 1
    assert cpu.total_cycles == 4
    print("✓ NOP instruction test passed")

def test_add_immediate():
    """Test ADD A,n (0xC6) instruction"""
    mem = Memory()
    mem.write_byte(0x0100, 0xC6)  # ADD A,n
    mem.write_byte(0x0101, 0x42)  # Immediate value 0x42
    
    cpu = CPU(mem)
    cpu.registers._a = 0x10
    
    cpu.step()
    
    assert cpu.registers._a == 0x52  # 0x10 + 0x42
    assert cpu.registers._pc == 0x0102  # PC advanced by 2
    assert cpu.total_cycles == 8
    print("✓ ADD A,n test passed")

def test_add_register():
    """Test ADD A,B (0x80) instruction"""
    mem = Memory()
    mem.write_byte(0x0100, 0x80)  # ADD A,B
    
    cpu = CPU(mem)
    cpu.registers._a = 0x05
    cpu.registers._b = 0x03
    
    cpu.step()
    
    assert cpu.registers._a == 0x08
    assert cpu.registers._pc == 0x0101
    assert cpu.total_cycles == 4
    print("✓ ADD A,B test passed")

def test_multiple_instructions():
    """Test running multiple instructions"""
    mem = Memory()
    mem.write_byte(0x0100, 0x00)  # NOP
    mem.write_byte(0x0101, 0x80)  # ADD A,B
    mem.write_byte(0x0102, 0x87)  # ADD A,A
    mem.write_byte(0x0103, 0x76)  # HALT
    
    cpu = CPU(mem)
    cpu.registers._a = 0x05
    cpu.registers._b = 0x03
    
    cpu.step()  # NOP
    assert cpu.registers._pc == 0x0101
    
    cpu.step()  # ADD A,B -> A = 0x08
    assert cpu.registers._a == 0x08
    
    cpu.step()  # ADD A,A -> A = 0x10
    assert cpu.registers._a == 0x10
    
    cpu.step()  # HALT
    assert cpu.halted == True
    
    print("✓ Multiple instructions test passed")

def test_run_until():
    """Test running for specified cycles"""
    mem = Memory()
    for i in range(20):
        mem.write_byte(0x0100 + i, 0x00)  # Fill with NOPs
    
    cpu = CPU(mem)
    cpu.run_until(40)  # Run for 40 cycles = 10 NOPs
    
    assert cpu.total_cycles == 40
    assert cpu.registers._pc == 0x010A  # 10 instructions executed
    print("✓ run_until test passed")

if __name__ == "__main__":
    test_nop_instruction()
    test_add_immediate()
    test_add_register()
    test_multiple_instructions()
    test_run_until()
    print("\n✓ All CPU loop tests passed!")
