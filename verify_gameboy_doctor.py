"""
Comprehensive verification of Gameboy Doctor integration

This script verifies that:
1. Normal mode works (Doctor disabled)
2. Doctor mode works (Doctor enabled)
3. Log format is correct
4. LY override works
5. CPU initialization works
"""

import os
import sys

# Fix Windows console encoding for checkmarks
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


def test_normal_mode():
    """Test that emulator works normally when Doctor is disabled"""
    print("=" * 70)
    print("TEST 1: Normal Mode (GAMEBOY_DOCTOR not set)")
    print("=" * 70)

    # Ensure Doctor mode is disabled
    if 'GAMEBOY_DOCTOR' in os.environ:
        del os.environ['GAMEBOY_DOCTOR']

    from src.cpu import CPU

    cpu = CPU()

    # Check logger is None
    if cpu._doctor_logger is not None:
        print("❌ FAILED: Logger should be None in normal mode")
        return False

    # Execute an instruction
    cpu.memory.write_byte(0x0100, 0x3C)  # INC A
    cpu.registers._pc = 0x0100
    cpu.registers._a = 42

    cpu.step()

    if cpu.registers._a != 43:
        print(f"❌ FAILED: A should be 43, got {cpu.registers._a}")
        return False

    # Check LY register works normally
    cpu.memory.write_byte(0xFF44, 0x50)
    ly = cpu.memory.read_byte(0xFF44)
    if ly != 0x50:
        print(f"❌ FAILED: LY should be 0x50, got 0x{ly:02X}")
        return False

    print("✅ PASSED: Normal mode works correctly")
    print(f"   - Logger is None")
    print(f"   - Instructions execute correctly")
    print(f"   - LY register works normally")
    return True


def test_doctor_mode():
    """Test that Doctor mode activates correctly"""
    print("\n" + "=" * 70)
    print("TEST 2: Doctor Mode (GAMEBOY_DOCTOR=1)")
    print("=" * 70)

    # Enable Doctor mode
    os.environ['GAMEBOY_DOCTOR'] = '1'

    # Need to reimport to pick up new environment
    import importlib
    import src.gameboy_doctor
    import src.cpu
    importlib.reload(src.gameboy_doctor)
    importlib.reload(src.cpu)

    from src.cpu import CPU

    cpu = CPU()

    # Check logger is created
    if cpu._doctor_logger is None:
        print("❌ FAILED: Logger should be created in Doctor mode")
        return False

    if not cpu._doctor_logger.enabled:
        print("❌ FAILED: Logger should be enabled")
        return False

    print("✅ PASSED: Doctor mode activates correctly")
    print(f"   - Logger is created")
    print(f"   - Logger is enabled")
    return True


def test_log_format():
    """Test that log format is correct"""
    print("\n" + "=" * 70)
    print("TEST 3: Log Format")
    print("=" * 70)

    os.environ['GAMEBOY_DOCTOR'] = '1'

    # Clear log file
    try:
        with open("emulator_log.txt", "w") as f:
            f.write("")
    except:
        pass

    import importlib
    import src.gameboy_doctor
    import src.cpu
    importlib.reload(src.gameboy_doctor)
    importlib.reload(src.cpu)

    from src.cpu import CPU
    from src.gameboy_doctor import initialize_cpu_for_doctor

    cpu = CPU()
    initialize_cpu_for_doctor(cpu)

    # Write a simple instruction
    cpu.memory.write_byte(0x0100, 0x00)  # NOP

    # Execute
    cpu.step()

    # Read log
    try:
        with open("emulator_log.txt", "r") as f:
            log_line = f.read().strip()
    except Exception as e:
        print(f"❌ FAILED: Could not read log: {e}")
        return False

    # Verify format
    # PC should be 0x0100 (where instruction WAS before fetch, not after)
    expected_format = "A:01 F:B0 B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0100 PCMEM:"
    if not log_line.startswith(expected_format):
        print(f"❌ FAILED: Log format incorrect")
        print(f"   Expected: {expected_format}...")
        print(f"   Got:      {log_line}")
        return False

    # Verify PC is correct (should be 0x0100 - where instruction was, not 0x0101)
    if "PC:0100" not in log_line:
        print(f"❌ FAILED: PC should be 0x0100 (before fetch)")
        print(f"   Got: {log_line}")
        return False

    print("✅ PASSED: Log format is correct")
    print(f"   Log: {log_line}")
    return True


def test_ly_override():
    """Test that LY register override works"""
    print("\n" + "=" * 70)
    print("TEST 4: LY Register Override")
    print("=" * 70)

    os.environ['GAMEBOY_DOCTOR'] = '1'

    import importlib
    import src.gameboy_doctor
    import src.cpu
    import src.memory
    importlib.reload(src.gameboy_doctor)
    importlib.reload(src.memory)
    importlib.reload(src.cpu)

    from src.cpu import CPU

    cpu = CPU()

    # Write something to LY
    cpu.memory.write_byte(0xFF44, 0x20)

    # Read LY - should get 0x90 in Doctor mode
    ly = cpu.memory.read_byte(0xFF44)

    if ly != 0x90:
        print(f"❌ FAILED: LY should return 0x90 in Doctor mode, got 0x{ly:02X}")
        return False

    print("✅ PASSED: LY override works correctly")
    print(f"   LY always returns 0x90 (VBlank)")
    return True


def test_cpu_initialization():
    """Test that CPU initialization to Doctor state works"""
    print("\n" + "=" * 70)
    print("TEST 5: CPU Initialization")
    print("=" * 70)

    os.environ['GAMEBOY_DOCTOR'] = '1'

    import importlib
    import src.gameboy_doctor
    import src.cpu
    importlib.reload(src.gameboy_doctor)
    importlib.reload(src.cpu)

    from src.cpu import CPU
    from src.gameboy_doctor import initialize_cpu_for_doctor

    cpu = CPU()
    initialize_cpu_for_doctor(cpu)

    # Verify register values
    checks = [
        ('A', cpu.registers._a, 0x01),
        ('B', cpu.registers._b, 0x00),
        ('C', cpu.registers._c, 0x13),
        ('D', cpu.registers._d, 0x00),
        ('E', cpu.registers._e, 0xD8),
        ('H', cpu.registers._h, 0x01),
        ('L', cpu.registers._l, 0x4D),
        ('SP', cpu.registers._sp, 0xFFFE),
        ('PC', cpu.registers._pc, 0x0100),
    ]

    all_passed = True
    for name, actual, expected in checks:
        if actual != expected:
            print(f"❌ {name} should be 0x{expected:02X}, got 0x{actual:02X}")
            all_passed = False

    # Check flags (F = 0xB0 = 10110000 = Z=1, N=0, H=1, C=1)
    if not cpu.registers.flags.zero:
        print("❌ Zero flag should be True")
        all_passed = False
    if cpu.registers.flags.subtract:
        print("❌ Subtract flag should be False")
        all_passed = False
    if not cpu.registers.flags.half_carry:
        print("❌ Half-carry flag should be True")
        all_passed = False
    if not cpu.registers.flags.carry:
        print("❌ Carry flag should be True")
        all_passed = False

    if all_passed:
        print("✅ PASSED: CPU initialization correct")
        print("   All registers match Blargg test state")
        print("   A=0x01 F=0xB0 B=0x00 C=0x13 D=0x00 E=0xD8")
        print("   H=0x01 L=0x4D SP=0xFFFE PC=0x0100")
    else:
        print("❌ FAILED: CPU initialization incorrect")

    return all_passed


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("GAMEBOY DOCTOR INTEGRATION VERIFICATION")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Normal Mode", test_normal_mode()))
    results.append(("Doctor Mode", test_doctor_mode()))
    results.append(("Log Format", test_log_format()))
    results.append(("LY Override", test_ly_override()))
    results.append(("CPU Initialization", test_cpu_initialization()))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 70)
    print(f"TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Gameboy Doctor integration is working correctly.")
        print("\nYou can now:")
        print("1. Download Blargg test ROMs")
        print("2. Run: python run_gameboy_doctor.py <test_rom.gb>")
        print("3. Compare logs with Gameboy Doctor tool")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
