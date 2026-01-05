"""
Test SUB instruction and carry flag
"""

from src.cpu import CPU

def test_sub_carry():
    print("Testing SUB instruction carry flag behavior")
    print("=" * 60)

    cpu = CPU()

    # Test 1: 10 - 5 = 5 (no carry/borrow)
    print("\nTest 1: A=10, SUB 5")
    cpu.registers._a = 10
    cpu._execute_sub('IMMEDIATE', 5)
    print(f"  Result: A={cpu.registers._a}")
    print(f"  Carry flag: {cpu.registers.flags.carry}")
    print(f"  Expected: A=5, Carry=False")
    assert cpu.registers._a == 5
    assert cpu.registers.flags.carry == False

    # Test 2: 5 - 10 = -5 (carry/borrow)
    print("\nTest 2: A=5, SUB 10")
    cpu.registers._a = 5
    cpu._execute_sub('IMMEDIATE', 10)
    print(f"  Result: A={cpu.registers._a}")
    print(f"  Carry flag: {cpu.registers.flags.carry}")
    print(f"  Expected: A=251 (wraps), Carry=True")
    assert cpu.registers._a == 251  # 5 - 10 = -5, wraps to 251
    assert cpu.registers.flags.carry == True

    # Test 3: 4 - 5 = -1 (carry/borrow) - the delay loop case!
    print("\nTest 3: A=4, SUB 5 (delay loop exit condition)")
    cpu.registers._a = 4
    cpu._execute_sub('IMMEDIATE', 5)
    print(f"  Result: A={cpu.registers._a}")
    print(f"  Carry flag: {cpu.registers.flags.carry}")
    print(f"  Expected: A=255 (wraps), Carry=True")
    print(f"  JR NC should NOT jump (carry is set)")
    assert cpu.registers._a == 255  # 4 - 5 = -1, wraps to 255
    assert cpu.registers.flags.carry == True

    print("\n" + "=" * 60)
    print("All tests passed!")

if __name__ == '__main__':
    test_sub_carry()
