from src.cpu import CPU
from src.memory import Memory


def _mem_with_program(program, start=0x0100):
    """Memory with `program` placed in ROM at `start` (ROM can't be written with write_byte)."""
    rom = bytearray(0x8000)
    rom[start:start + len(program)] = bytes(program)
    mem = Memory()
    mem.load_rom(bytes(rom))
    return mem

def test_nop_instruction():
    """Test NOP (0x00) instruction"""
    mem = _mem_with_program([0x00])
    
    cpu = CPU(mem)
    initial_pc = cpu.registers._pc
    
    cpu.step()
    
    assert cpu.registers._pc == initial_pc + 1
    assert cpu.total_cycles == 4
    print("✓ NOP instruction test passed")

def test_add_immediate():
    """Test ADD A,n (0xC6) instruction"""
    mem = _mem_with_program([0xC6, 0x42])
    
    cpu = CPU(mem)
    cpu.registers._a = 0x10
    
    cpu.step()
    
    assert cpu.registers._a == 0x52  # 0x10 + 0x42
    assert cpu.registers._pc == 0x0102  # PC advanced by 2
    assert cpu.total_cycles == 8
    print("✓ ADD A,n test passed")

def test_add_register():
    """Test ADD A,B (0x80) instruction"""
    mem = _mem_with_program([0x80])
    
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
    mem = _mem_with_program([0x00, 0x80, 0x87, 0x76])
    
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
    mem = _mem_with_program([0x00] * 20)  # 20 NOPs

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
