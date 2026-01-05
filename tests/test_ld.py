"""Tests for LD (load) instructions"""
import pytest
from src.cpu import CPU
from src.memory import Memory

def test_ld_immediate_to_register():
    """Test LD B,n - Load immediate into register"""
    mem = Memory()
    mem.write_byte(0x0100, 0x06)  # LD B,n
    mem.write_byte(0x0101, 0x42)  # n = 0x42
    
    cpu = CPU(mem)
    cpu.step()
    
    assert cpu.registers._b == 0x42
    assert cpu.registers._pc == 0x0102

def test_ld_register_to_register():
    """Test LD A,B - Copy register to register"""
    mem = Memory()
    mem.write_byte(0x0100, 0x78)  # LD A,B
    
    cpu = CPU(mem)
    cpu.registers._b = 0x99
    cpu.step()
    
    assert cpu.registers._a == 0x99
    assert cpu.registers._b == 0x99  # B unchanged

def test_ld_16bit_immediate():
    """Test LD HL,nn - Load 16-bit immediate"""
    mem = Memory()
    mem.write_byte(0x0100, 0x21)  # LD HL,nn
    mem.write_byte(0x0101, 0x34)  # Low byte
    mem.write_byte(0x0102, 0x12)  # High byte
    
    cpu = CPU(mem)
    cpu.step()
    
    assert cpu.registers.hl == 0x1234
    assert cpu.registers._h == 0x12
    assert cpu.registers._l == 0x34

def test_ld_from_memory():
    """Test LD A,(HL) - Load from memory"""
    mem = Memory()
    mem.write_byte(0x0100, 0x7E)  # LD A,(HL)
    mem.write_byte(0x5000, 0xAB)  # Data at 0x5000
    
    cpu = CPU(mem)
    cpu.registers.hl = 0x5000
    cpu.step()
    
    assert cpu.registers._a == 0xAB

def test_ld_to_memory():
    """Test LD (HL),A - Store to memory"""
    mem = Memory()
    mem.write_byte(0x0100, 0x77)  # LD (HL),A
    
    cpu = CPU(mem)
    cpu.registers._a = 0xCD
    cpu.registers.hl = 0x6000
    cpu.step()
    
    assert mem.read_byte(0x6000) == 0xCD

@pytest.mark.parametrize("opcode,reg_name,expected", [
    (0x06, '_b', 0x12),  # LD B,n
    (0x0E, '_c', 0x34),  # LD C,n
    (0x16, '_d', 0x56),  # LD D,n
    (0x1E, '_e', 0x78),  # LD E,n
    (0x26, '_h', 0x9A),  # LD H,n
    (0x2E, '_l', 0xBC),  # LD L,n
    (0x3E, '_a', 0xDE),  # LD A,n
])
def test_ld_immediate_all_registers(opcode, reg_name, expected):
    """Test all LD r,n instructions"""
    mem = Memory()
    mem.write_byte(0x0100, opcode)
    mem.write_byte(0x0101, expected)
    
    cpu = CPU(mem)
    cpu.step()
    
    assert getattr(cpu.registers, reg_name) == expected

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
