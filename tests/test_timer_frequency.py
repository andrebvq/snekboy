"""
Test timer frequency accuracy
"""

from src.cpu import CPU

def test_timer_frequency_256():
    """Test TIMA increments every 256 M-cycles at freq=00"""
    cpu = CPU()

    # Setup timer: freq=00 (256 M-cycles), enabled
    cpu.memory.write_byte(0xFF05, 0x00)  # TIMA = 0
    cpu.memory.write_byte(0xFF07, 0x04)  # TAC = enable, freq 00

    print("Test: Frequency 00 (256 M-cycles)")

    # Run for 256 cycles - should increment TIMA by 1
    cpu._update_timers(256)
    tima = cpu.memory.read_byte(0xFF05)
    print(f"  After 256 cycles: TIMA = {tima} (expected: 1)")

    # Run for another 256 cycles
    cpu._update_timers(256)
    tima = cpu.memory.read_byte(0xFF05)
    print(f"  After 512 cycles: TIMA = {tima} (expected: 2)")

    assert tima == 2, f"Expected TIMA=2, got {tima}"
    print("[PASS]")

def test_timer_frequency_4():
    """Test TIMA increments every 4 M-cycles at freq=01"""
    cpu = CPU()

    # Setup timer: freq=01 (4 M-cycles), enabled
    cpu.memory.write_byte(0xFF05, 0x00)  # TIMA = 0
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC = enable, freq 01

    print("\nTest: Frequency 01 (4 M-cycles)")

    # Run for 4 cycles - should increment TIMA by 1
    cpu._update_timers(4)
    tima = cpu.memory.read_byte(0xFF05)
    print(f"  After 4 cycles: TIMA = {tima} (expected: 1)")

    # Run for 20 more cycles = 5 more increments
    cpu._update_timers(20)
    tima = cpu.memory.read_byte(0xFF05)
    print(f"  After 24 cycles: TIMA = {tima} (expected: 6)")

    assert tima == 6, f"Expected TIMA=6, got {tima}"
    print("[PASS]")

def test_div_frequency():
    """Test DIV increments every 64 M-cycles"""
    cpu = CPU()

    # Reset DIV
    cpu.memory.write_byte(0xFF04, 0x00)

    print("\nTest: DIV frequency (64 M-cycles)")

    # Run for 64 cycles
    cpu._update_timers(64)
    div = cpu.memory.read_byte(0xFF04)
    print(f"  After 64 cycles: DIV = 0x{div:02X} (expected: 0x01)")

    # Run for 64 more cycles
    cpu._update_timers(64)
    div = cpu.memory.read_byte(0xFF04)
    print(f"  After 128 cycles: DIV = 0x{div:02X} (expected: 0x02)")

    assert div == 0x02, f"Expected DIV=0x02, got 0x{div:02X}"
    print("[PASS]")

if __name__ == '__main__':
    print("="*60)
    print("TIMER FREQUENCY TESTS")
    print("="*60)

    try:
        test_timer_frequency_256()
        test_timer_frequency_4()
        test_div_frequency()

        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
