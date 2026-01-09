"""
Test conditional branch cycle timing

Verify that conditional jumps/calls/returns use correct cycle counts
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.memory import Memory

def test_jr_conditional_taken():
    """JR Z,n when Z flag is set (jump taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = True  # Set Z flag

    # JR Z,+5
    cpu.memory.write_byte(0x0100, 0x28)  # JR Z,n
    cpu.memory.write_byte(0x0101, 0x05)  # offset = 5

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 12, f"JR Z,n (taken) should use 12 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0107, f"PC should be 0x0107, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: JR Z,n (taken): {cycles_used} cycles")

def test_jr_conditional_not_taken():
    """JR Z,n when Z flag is clear (jump not taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = False  # Clear Z flag

    # JR Z,+5
    cpu.memory.write_byte(0x0100, 0x28)  # JR Z,n
    cpu.memory.write_byte(0x0101, 0x05)  # offset = 5

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 8, f"JR Z,n (not taken) should use 8 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0102, f"PC should be 0x0102, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: JR Z,n (not taken): {cycles_used} cycles")

def test_jr_unconditional():
    """JR n (unconditional)"""
    cpu = CPU()

    # JR +5
    cpu.memory.write_byte(0x0100, 0x18)  # JR n
    cpu.memory.write_byte(0x0101, 0x05)  # offset = 5

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 12, f"JR n should use 12 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0107, f"PC should be 0x0107, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: JR n (unconditional): {cycles_used} cycles")

def test_jp_conditional_taken():
    """JP Z,nn when Z flag is set (jump taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = True  # Set Z flag

    # JP Z,0x1234
    cpu.memory.write_byte(0x0100, 0xCA)  # JP Z,nn
    cpu.memory.write_byte(0x0101, 0x34)  # low byte
    cpu.memory.write_byte(0x0102, 0x12)  # high byte

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 16, f"JP Z,nn (taken) should use 16 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x1234, f"PC should be 0x1234, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: JP Z,nn (taken): {cycles_used} cycles")

def test_jp_conditional_not_taken():
    """JP Z,nn when Z flag is clear (jump not taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = False  # Clear Z flag

    # JP Z,0x1234
    cpu.memory.write_byte(0x0100, 0xCA)  # JP Z,nn
    cpu.memory.write_byte(0x0101, 0x34)  # low byte
    cpu.memory.write_byte(0x0102, 0x12)  # high byte

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 12, f"JP Z,nn (not taken) should use 12 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0103, f"PC should be 0x0103, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: JP Z,nn (not taken): {cycles_used} cycles")

def test_ret_conditional_taken():
    """RET Z when Z flag is set (return taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = True  # Set Z flag
    cpu.registers._sp = 0xFFFE

    # Set up stack to return to 0x1234
    cpu.memory.write_byte(0xFFFE, 0x34)  # low byte
    cpu.memory.write_byte(0xFFFF, 0x12)  # high byte

    # RET Z
    cpu.memory.write_byte(0x0100, 0xC8)  # RET Z

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 20, f"RET Z (taken) should use 20 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x1234, f"PC should be 0x1234, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: RET Z (taken): {cycles_used} cycles")

def test_ret_conditional_not_taken():
    """RET Z when Z flag is clear (return not taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = False  # Clear Z flag
    cpu.registers._sp = 0xFFFE

    # RET Z
    cpu.memory.write_byte(0x0100, 0xC8)  # RET Z

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 8, f"RET Z (not taken) should use 8 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0101, f"PC should be 0x0101, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: RET Z (not taken): {cycles_used} cycles")

def test_ret_unconditional():
    """RET (unconditional)"""
    cpu = CPU()
    cpu.registers._sp = 0xFFFE

    # Set up stack to return to 0x1234
    cpu.memory.write_byte(0xFFFE, 0x34)  # low byte
    cpu.memory.write_byte(0xFFFF, 0x12)  # high byte

    # RET
    cpu.memory.write_byte(0x0100, 0xC9)  # RET

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 16, f"RET should use 16 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x1234, f"PC should be 0x1234, got 0x{cpu.registers._pc:04X}"
    print(f"PASS: RET (unconditional): {cycles_used} cycles")

def test_call_conditional_taken():
    """CALL Z,nn when Z flag is set (call taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = True  # Set Z flag
    cpu.registers._sp = 0xFFFE

    # CALL Z,0x1234
    cpu.memory.write_byte(0x0100, 0xCC)  # CALL Z,nn
    cpu.memory.write_byte(0x0101, 0x34)  # low byte
    cpu.memory.write_byte(0x0102, 0x12)  # high byte

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 24, f"CALL Z,nn (taken) should use 24 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x1234, f"PC should be 0x1234, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xFFFC, f"SP should be 0xFFFC, got 0x{cpu.registers._sp:04X}"
    print(f"PASS: CALL Z,nn (taken): {cycles_used} cycles")

def test_call_conditional_not_taken():
    """CALL Z,nn when Z flag is clear (call not taken)"""
    cpu = CPU()
    cpu.registers.flags.zero = False  # Clear Z flag
    cpu.registers._sp = 0xFFFE

    # CALL Z,0x1234
    cpu.memory.write_byte(0x0100, 0xCC)  # CALL Z,nn
    cpu.memory.write_byte(0x0101, 0x34)  # low byte
    cpu.memory.write_byte(0x0102, 0x12)  # high byte

    initial_cycles = cpu.total_cycles
    cpu.step()
    cycles_used = cpu.total_cycles - initial_cycles

    assert cycles_used == 12, f"CALL Z,nn (not taken) should use 12 cycles, got {cycles_used}"
    assert cpu.registers._pc == 0x0103, f"PC should be 0x0103, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xFFFE, f"SP should be 0xFFFE, got 0x{cpu.registers._sp:04X}"
    print(f"PASS: CALL Z,nn (not taken): {cycles_used} cycles")

if __name__ == "__main__":
    print("Testing conditional branch cycle timing...")
    print()

    test_jr_unconditional()
    test_jr_conditional_taken()
    test_jr_conditional_not_taken()
    print()

    test_jp_conditional_taken()
    test_jp_conditional_not_taken()
    print()

    test_ret_unconditional()
    test_ret_conditional_taken()
    test_ret_conditional_not_taken()
    print()

    test_call_conditional_taken()
    test_call_conditional_not_taken()
    print()

    print("=" * 60)
    print("ALL CONDITIONAL CYCLE TESTS PASSED!")
    print("=" * 60)
