# tests.py - add to test_add_instruction():
from src.cpu import CPU, ArithmeticTarget, Instruction, InstructionType
from src.registers import Register

def test_add_a_to_a():
    """Test ADD A,A instruction"""
    cpu = CPU()
    cpu.registers._a = 5
    
    instruction = Instruction(type=InstructionType.ADD, target=ArithmeticTarget.A)
    cpu.execute(instruction)
    
    assert cpu.registers._a == 10, "ADD A,A should double the value"
    print("ADD A,A test passed!")


def test_af_register_pair():
    reg = Register()
    
    # Test getter
    reg._a = 0x12
    reg.flags.from_byte(0xB0)
    assert reg.af == 0x12B0, f"Expected 0x12B0, got {reg.af:04X}"
    
    # Test setter
    reg.af = 0xABCD
    assert reg._a == 0xAB, f"Expected A=0xAB, got {reg._a:02X}"
    assert reg.flags.to_byte() == 0xCD, f"Expected F=0xCD, got {reg.flags.to_byte():02X}"
    
    print("✓ AF register pair test passed")

def test_bc_register_pair():
    reg = Register()
    
    reg._b = 0x12
    reg._c = 0x34
    assert reg.bc == 0x1234
    
    reg.bc = 0x5678
    assert reg._b == 0x56
    assert reg._c == 0x78
    
    print("✓ BC register pair test passed")

def test_de_register_pair():
    reg = Register()
    reg.de = 0xABCD
    assert reg._d == 0xAB
    assert reg._e == 0xCD
    print("✓ DE register pair test passed")

def test_hl_register_pair():
    reg = Register()
    reg.hl = 0x1234
    assert reg._h == 0x12
    assert reg._l == 0x34
    print("✓ HL register pair test passed")


test_af_register_pair()
test_bc_register_pair()
test_de_register_pair()
test_hl_register_pair()
print("\n✓ All register pair tests passed!")

test_add_a_to_a()