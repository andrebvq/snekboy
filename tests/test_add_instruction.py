"""
Test ADD instruction through the full CPU pipeline
"""

from src.cpu import CPU
from src.memory import Memory

def test_add_through_rom():
    """Test ADD by loading a minimal ROM"""
    cpu = CPU()

    # Create a minimal ROM that does: ADD A, 1
    # Opcode 0xC6 is ADD A,n (immediate)
    rom = bytearray([
        0xC6, 0x01,  # ADD A, 1
        0x76,        # HALT
    ])

    cpu.memory.load_rom(rom)

    # Initialize A to 0
    cpu.registers._a = 0
    cpu.registers._pc = 0

    print(f"Before: A = 0x{cpu.registers._a:02X}")

    # Execute one instruction (ADD A, 1)
    cpu.step()

    print(f"After ADD A,1: A = 0x{cpu.registers._a:02X} (expected: 0x01)")
    print(f"Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")

    if cpu.registers._a == 1:
        print("[PASS] ADD instruction works!")
        return True
    else:
        print(f"[FAIL] ADD instruction failed: Expected 1, got {cpu.registers._a}")
        return False

def test_add_ascii():
    """Test adding to ASCII '0' to get '1'"""
    cpu = CPU()

    # ADD A, 1 where A = 0x30
    rom = bytearray([
        0x3E, 0x30,  # LD A, 0x30
        0xC6, 0x01,  # ADD A, 1
        0x76,        # HALT
    ])

    cpu.memory.load_rom(rom)
    cpu.registers._pc = 0

    # Execute LD A, 0x30
    cpu.step()
    print(f"\nAfter LD A,0x30: A = 0x{cpu.registers._a:02X}")

    # Execute ADD A, 1
    cpu.step()
    result = cpu.registers._a
    char = chr(result) if 32 <= result < 127 else '?'

    print(f"After ADD A,1: A = 0x{result:02X} = '{char}' (expected: 0x31 = '1')")

    if result == 0x31:
        print("[PASS] ASCII conversion works!")
        return True
    else:
        print(f"[FAIL] Expected 0x31, got 0x{result:02X}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("ADD INSTRUCTION TESTS (through ROM)")
    print("="*60)

    test_add_through_rom()
    test_add_ascii()
