"""
Test that CALL instruction works correctly when executed from RAM

This will verify that the CALL instruction properly reads its operand bytes
and jumps to the correct address.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_call_from_ram():
    cpu = CPU()

    # Load a minimal ROM (just to initialize properly)
    for i in range(0x100):
        cpu.memory.write_byte(i, 0x00)  # NOPs

    # Set up code in RAM at 0xC000
    # We'll create a CALL instruction that should call 0xC100
    cpu.memory.write_byte(0xC000, 0xCD)  # CALL nn
    cpu.memory.write_byte(0xC001, 0x00)  # Low byte: 0x00
    cpu.memory.write_byte(0xC002, 0xC1)  # High byte: 0xC1 -> address 0xC100
    cpu.memory.write_byte(0xC003, 0x00)  # NOP after CALL

    # Put a simple routine at 0xC100
    cpu.memory.write_byte(0xC100, 0x3C)  # INC A
    cpu.memory.write_byte(0xC101, 0xC9)  # RET

    # Set up initial state
    cpu.registers._pc = 0xC000
    cpu.registers._sp = 0xDFFF
    cpu.registers._a = 0x42

    print("Initial state:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  SP=0x{cpu.registers._sp:04X}")
    print(f"  A=0x{cpu.registers._a:02X}")
    print()

    # Execute CALL
    print("Executing CALL at 0xC000...")
    cpu.step()

    print(f"After CALL:")
    print(f"  PC=0x{cpu.registers._pc:04X} (should be 0xC100)")
    print(f"  SP=0x{cpu.registers._sp:04X} (should be 0xDFFD)")
    print()

    # Check return address on stack
    ret_low = cpu.memory.read_byte(0xDFFD)
    ret_high = cpu.memory.read_byte(0xDFFE)
    ret_addr = ret_low | (ret_high << 8)
    print(f"Return address on stack: 0x{ret_addr:04X} (should be 0xC003)")
    print()

    # Execute INC A
    print("Executing INC A at 0xC100...")
    cpu.step()
    print(f"  A=0x{cpu.registers._a:02X} (should be 0x43)")
    print()

    # Execute RET
    print("Executing RET at 0xC101...")
    cpu.step()
    print(f"After RET:")
    print(f"  PC=0x{cpu.registers._pc:04X} (should be 0xC003)")
    print(f"  SP=0x{cpu.registers._sp:04X} (should be 0xDFFF)")
    print()

    # Verify
    assert cpu.registers._pc == 0xC003, f"PC should be 0xC003, got 0x{cpu.registers._pc:04X}"
    assert cpu.registers._sp == 0xDFFF, f"SP should be 0xDFFF, got 0x{cpu.registers._sp:04X}"
    assert cpu.registers._a == 0x43, f"A should be 0x43, got 0x{cpu.registers._a:02X}"

    print("=" * 80)
    print("PASS: CALL from RAM works correctly!")
    print("=" * 80)

if __name__ == "__main__":
    test_call_from_ram()
