"""
Debug test to verify basic arithmetic operations
"""

from src.cpu import CPU
from src.memory import Memory

def test_basic_add():
    """Test that 0 + 1 = 1, not 0xF7"""
    cpu = CPU()

    # Set A = 0
    cpu.registers._a = 0

    # Execute: ADD A, 1
    cpu._execute_add(None, 1)  # Using immediate value

    result = cpu.registers._a
    print(f"Test: 0 + 1 = {result} (expected: 1, got: 0x{result:02X})")

    if result == 1:
        print("[PASS] Basic ADD works correctly")
        return True
    else:
        print(f"[FAIL] Basic ADD FAILED: Expected 1, got {result} (0x{result:02X})")
        print(f"  Offset from expected: 0x{result - 1:02X}")
        return False

def test_add_with_ascii():
    """Test adding to get ASCII '1' (0x31)"""
    cpu = CPU()

    # ASCII '0' = 0x30
    cpu.registers._a = 0x30

    # Add 1 to get ASCII '1' = 0x31
    cpu._execute_add(None, 1)

    result = cpu.registers._a
    print(f"\nTest: 0x30 + 1 = 0x{result:02X} (expected: 0x31 which is '{chr(result) if 32 <= result < 127 else '?'}')")

    if result == 0x31:
        print("[PASS] ASCII arithmetic works correctly")
        return True
    else:
        print(f"[FAIL] ASCII arithmetic FAILED: Expected 0x31, got 0x{result:02X}")
        print(f"  Character: '{chr(result) if 32 <= result < 127 else '?'}'")
        return False

def test_inc_operations():
    """Test INC instruction"""
    cpu = CPU()

    # Test INC A from 0
    cpu.registers._a = 0
    cpu._execute_inc('A')

    result = cpu.registers._a
    print(f"\nTest: INC A (from 0) = {result} (expected: 1)")

    if result == 1:
        print("[PASS] INC A works correctly")
        return True
    else:
        print(f"[FAIL] INC A FAILED: Expected 1, got {result} (0x{result:02X})")
        return False

def test_daa_simple():
    """Test DAA with simple case"""
    cpu = CPU()

    # Set A = 0x09, add 1, then DAA
    cpu.registers._a = 0x09
    cpu._execute_add(None, 1)  # Should give 0x0A

    print(f"\nBefore DAA: A = 0x{cpu.registers._a:02X}")
    print(f"  Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")

    cpu._execute_daa()

    result = cpu.registers._a
    print(f"After DAA: A = 0x{result:02X} (expected: 0x10 for BCD)")
    print(f"  Flags: Z={cpu.registers.flags.zero}, N={cpu.registers.flags.subtract}, H={cpu.registers.flags.half_carry}, C={cpu.registers.flags.carry}")

    if result == 0x10:
        print("[PASS] DAA works correctly")
        return True
    else:
        print(f"[FAIL] DAA result: Expected 0x10, got 0x{result:02X}")
        return False

def test_character_conversion():
    """Test converting digit to ASCII character"""
    cpu = CPU()

    # Start with digit 1
    cpu.registers._a = 1

    # Add ASCII '0' (0x30) to get ASCII '1' (0x31)
    cpu._execute_add(None, 0x30)

    result = cpu.registers._a
    char = chr(result) if 32 <= result < 127 else '?'
    print(f"\nTest: 1 + 0x30 = 0x{result:02X} = '{char}' (expected: 0x31 = '1')")

    if result == 0x31:
        print("[PASS] Digit to ASCII conversion works")
        return True
    else:
        print(f"[FAIL] Conversion FAILED: Expected 0x31 ('1'), got 0x{result:02X} ('{char}')")
        if result == 0xF7:
            print("  [WARN]  THIS IS THE EXACT ERROR WE SAW IN BLARGG OUTPUT!")
            print(f"  Difference: 0x{result - 0x31:02X} = {result - 0x31} decimal")
        return False

def test_bcd_digit():
    """Test BCD digit increment like Blargg test might do"""
    cpu = CPU()

    # Set A = 0x00 (BCD zero)
    cpu.registers._a = 0x00

    # Add 1
    cpu._execute_add(None, 1)
    print(f"\n0x00 + 1 = 0x{cpu.registers._a:02X}")

    # Apply DAA
    cpu._execute_daa()
    print(f"After DAA: 0x{cpu.registers._a:02X}")

    # Now add ASCII '0' to convert to character
    cpu._execute_add(None, 0x30)
    result = cpu.registers._a
    char = chr(result) if 32 <= result < 127 else f'[{result:02X}]'

    print(f"After adding 0x30: 0x{result:02X} = {char}")
    print(f"Expected: 0x31 = '1'")

    if result == 0x31:
        print("[PASS] BCD digit conversion works")
        return True
    else:
        print(f"[FAIL] BCD digit conversion FAILED")
        return False

if __name__ == '__main__':
    print("="*60)
    print("ARITHMETIC DEBUG TESTS")
    print("="*60)

    tests = [
        ("Basic ADD", test_basic_add),
        ("ASCII arithmetic", test_add_with_ascii),
        ("INC operation", test_inc_operations),
        ("DAA simple", test_daa_simple),
        ("Character conversion", test_character_conversion),
        ("BCD digit conversion", test_bcd_digit),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"[FAIL] {name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "[PASS] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} passed")
