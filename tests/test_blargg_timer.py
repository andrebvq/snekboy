"""
Test that mimics Blargg's test 02-04 (timer test)
"""

from src.cpu import CPU

def test_blargg_timer_scenario():
    """
    Mimic what Blargg test 04 does:
    1. Set TAC = $05 (enable timer, freq 01 = 4 M-cycles)
    2. Set TIMA = 0
    3. Set IF = 0
    4. Wait 500 cycles
    5. Check IF bit 2
    6. Wait another 500 cycles
    7. Check IF bit 2 again
    """
    cpu = CPU()

    print("Blargg Timer Test Simulation")
    print("="*60)

    # Step 1: Set TAC = $05
    cpu.memory.write_byte(0xFF07, 0x05)
    print("Set TAC = 0x05 (enable, freq 01 = 4 M-cycles)")

    # Step 2: Set TIMA = 0
    cpu.memory.write_byte(0xFF05, 0x00)
    print("Set TIMA = 0x00")

    # Step 3: Set IF = 0
    cpu.memory.write_byte(0xFF0F, 0x00)
    print("Set IF = 0x00")

    # Step 4: Wait 500 cycles
    print("\nWaiting 500 cycles...")
    cpu._update_timers(500)

    tima = cpu.memory.read_byte(0xFF05)
    if_reg = cpu.memory.read_byte(0xFF0F)
    timer_flag = (if_reg >> 2) & 1

    print(f"After 500 cycles:")
    print(f"  TIMA = 0x{tima:02X} (expected: ~125, since 500/4 = 125)")
    print(f"  IF = 0x{if_reg:02X}, timer bit = {timer_flag}")

    # With freq 01 (4 M-cycles), after 500 cycles:
    # TIMA should have incremented 125 times (500 / 4 = 125)
    # Starting from 0, TIMA should be at 125
    # Should NOT have overflowed yet (overflow at 256)

    expected_tima_approx = 125
    if abs(tima - expected_tima_approx) > 5:
        print(f"  [WARN] TIMA value unexpected! Expected ~{expected_tima_approx}, got {tima}")

    if timer_flag:
        print("  [WARN] Timer interrupt flag already set! Should not overflow yet.")

    # Step 5: Wait another 500 cycles (total 1000)
    print("\nWaiting another 500 cycles (total 1000)...")
    cpu._update_timers(500)

    tima = cpu.memory.read_byte(0xFF05)
    if_reg = cpu.memory.read_byte(0xFF0F)
    timer_flag = (if_reg >> 2) & 1

    print(f"After 1000 cycles total:")
    print(f"  TIMA = 0x{tima:02X}")
    print(f"  IF = 0x{if_reg:02X}, timer bit = {timer_flag}")

    # After 1000 cycles with freq 01:
    # TIMA would have incremented 250 times (1000 / 4 = 250)
    # Starting from 0: 0 + 250 = 250
    # Still should NOT have overflowed (overflow at 256)

    if timer_flag:
        print("  [WARN] Timer interrupt flag set at 1000 cycles")
        print("  With freq 01, should overflow after 256*4 = 1024 cycles")

    # Let's go a bit further to see the overflow
    print("\nWaiting another 100 cycles (total 1100)...")
    cpu._update_timers(100)

    tima = cpu.memory.read_byte(0xFF05)
    if_reg = cpu.memory.read_byte(0xFF0F)
    timer_flag = (if_reg >> 2) & 1

    print(f"After 1100 cycles total:")
    print(f"  TIMA = 0x{tima:02X}")
    print(f"  IF = 0x{if_reg:02X}, timer bit = {timer_flag}")

    # After 1100 cycles: 1100 / 4 = 275 increments
    # 275 > 256, so should have overflowed
    # After overflow: TIMA loads from TMA (which is 0), so TIMA = 0
    # And timer interrupt flag should be set

    if timer_flag:
        print("  [PASS] Timer interrupt flag correctly set after overflow")
        return True
    else:
        print("  [FAIL] Timer interrupt flag NOT set after overflow!")
        return False

if __name__ == '__main__':
    print("="*60)
    print("BLARGG TIMER TEST SIMULATION")
    print("="*60)

    try:
        result = test_blargg_timer_scenario()
        print("\n" + "="*60)
        if result:
            print("TEST PASSED")
        else:
            print("TEST FAILED")
        print("="*60)
    except Exception as e:
        print(f"\n[FAIL] Test crashed: {e}")
        import traceback
        traceback.print_exc()
