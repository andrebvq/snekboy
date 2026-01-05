"""
Test timer interrupt functionality
"""

from src.cpu import CPU

def test_timer_interrupt():
    """Test that timer overflow triggers interrupt"""
    cpu = CPU()

    print("Test: Timer overflow triggers interrupt")

    # Setup: Enable timer interrupt in IE
    cpu.memory.write_byte(0xFFFF, 0x04)  # IE: Enable timer interrupt (bit 2)

    # Setup timer to overflow quickly
    cpu.memory.write_byte(0xFF05, 0xFE)  # TIMA = 254 (will overflow after 2 increments)
    cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0 (reload value)
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC = enable timer, freq 01 (16 cycles/tick)

    # Enable interrupts
    cpu.ime = True

    # Setup a simple interrupt handler at 0x0050 (timer vector)
    # Just put a RET instruction (0xC9)
    cpu.memory.write_byte(0x0050, 0xC9)  # RET

    print(f"Initial state:")
    print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  IME: {cpu.ime}")

    # Run timer updates (32 cycles = 2 ticks at freq 01)
    cpu._update_timers(32)

    tima = cpu.memory.read_byte(0xFF05)
    if_val = cpu.memory.read_byte(0xFF0F)

    print(f"\nAfter 32 cycles:")
    print(f"  TIMA: 0x{tima:02X} (expected: 0x00 after overflow)")
    print(f"  IF: 0x{if_val:02X} (expected: 0x04, timer bit set)")

    if if_val & 0x04:
        print("[PASS] Timer interrupt flag set correctly")
        return True
    else:
        print("[FAIL] Timer interrupt flag not set")
        return False

if __name__ == '__main__':
    print("="*60)
    print("TIMER INTERRUPT TEST")
    print("="*60)

    try:
        test_timer_interrupt()
    except Exception as e:
        print(f"\n[FAIL] Test crashed: {e}")
        import traceback
        traceback.print_exc()
