"""
Unit Tests - Core component testing

Run specific unit tests with: python tests/run_unit_tests.py <test_name>
Run all unit tests with: python tests/run_unit_tests.py all
"""

import sys
import subprocess

UNIT_TESTS = {
    "cpu": "tests/test_cpu.py",
    "memory": "tests/test_memory.py",
    "registers": "tests/tests.py",  # Contains register tests
    "interrupts": "tests/test_interrupts.py",
    "interrupt_instructions": "tests/test_interrupt_instructions.py",
    "timer": "tests/test_timer.py",
    "joypad": "tests/test_joypad.py",
    "ppu": "tests/test_ppu_basic.py",
}

def run_test(name):
    if name not in UNIT_TESTS:
        print(f"Unknown test: {name}")
        print(f"Available tests: {', '.join(UNIT_TESTS.keys())}")
        return False

    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}\n")

    result = subprocess.run(
        ["python", UNIT_TESTS[name]],
        capture_output=False
    )

    return result.returncode == 0

def main():
    if len(sys.argv) < 2:
        print("Unit Test Suite")
        print("="*70)
        print("\nAvailable tests:")
        for name in UNIT_TESTS.keys():
            print(f"  - {name}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} <test_name>")
        print(f"  python {sys.argv[0]} all")
        return

    test_name = sys.argv[1]

    if test_name == "all":
        print("Running ALL unit tests...")
        passed = 0
        failed = 0

        for name in UNIT_TESTS.keys():
            if run_test(name):
                passed += 1
            else:
                failed += 1

        print(f"\n{'='*70}")
        print(f"SUMMARY: {passed} passed, {failed} failed")
        print(f"{'='*70}")

        sys.exit(0 if failed == 0 else 1)
    else:
        success = run_test(test_name)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
