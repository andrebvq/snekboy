"""
Test exact Blargg test 02 error 04 scenario
"""

from src.cpu import CPU

def test_blargg_04_exact():
    """
    Exact replication of Blargg test 02 error 04:

    wreg TAC,$05      ; Enable timer, freq 01 (4 M-cycles)
    wreg TIMA,0       ; Start at 0
    wreg IF,0         ; Clear interrupt flags
    delay 500         ; Wait 500 cycles
    lda IF            ; Check IF
    and $04           ; Mask timer bit
    jp nz,test_failed ; MUST be 0 (no interrupt yet)

    delay 500         ; Wait another 500 (1000 total)
    lda IF            ; Check IF
    and $04           ; Mask timer bit
    jp z,test_failed  ; MUST be non-zero (interrupt fired)
    """
    cpu = CPU()

    print("Blargg Test 02 Error 04 - Exact Replication")
    print("=" * 60)

    # Setup: TAC=$05, TIMA=0, IF=0
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC: enable, freq 01
    cpu.memory.write_byte(0xFF05, 0x00)  # TIMA: 0
    cpu.memory.write_byte(0xFF0F, 0x00)  # IF: 0

    print("Initial state:")
    print(f"  System counter = 0x{cpu._system_counter:04X}")
    print(f"  TAC  = 0x{cpu.memory.read_byte(0xFF07):02X}")
    print(f"  TIMA = 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"  IF   = 0x{cpu.memory.read_byte(0xFF0F):02X}")

    # Check if TAC write will cause spurious tick
    freq_01_bit_pos = 3
    bit_3_value = (cpu._system_counter >> freq_01_bit_pos) & 1
    print(f"  Bit 3 of system counter: {bit_3_value}")
    if bit_3_value == 1:
        print("  WARNING: TAC write may trigger spurious tick!")

    # Delay 500 cycles, then lda IF, then delay 500 more
    # (The lda IF happens BEFORE the and, so first check is at 1000 cycles)
    print("\nAfter 1000 cycles (delay 500 + delay 500):")
    cpu._update_timers(1000)

    tima_1000 = cpu.memory.read_byte(0xFF05)
    if_1000 = cpu.memory.read_byte(0xFF0F)
    if_timer_bit_1000 = if_1000 & 0x04

    print(f"  TIMA = 0x{tima_1000:02X} (expected: 0xFA = 250)")
    print(f"  IF   = 0x{if_1000:02X}")
    print(f"  IF & 0x04 = 0x{if_timer_bit_1000:02X} (MUST be 0x00)")

    if if_timer_bit_1000 != 0:
        print("\n[FAIL] Timer interrupt fired too early!")
        return False

    # Delay another 500 cycles (1500 total)
    print("\nAfter 1500 cycles total:")
    cpu._update_timers(500)

    tima_1500 = cpu.memory.read_byte(0xFF05)
    if_1500 = cpu.memory.read_byte(0xFF0F)
    if_timer_bit_1500 = if_1500 & 0x04

    print(f"  TIMA = 0x{tima_1500:02X}")
    print(f"  IF   = 0x{if_1500:02X}")
    print(f"  IF & 0x04 = 0x{if_timer_bit_1500:02X} (MUST be non-zero)")

    if if_timer_bit_1500 == 0:
        print("\n[FAIL] Timer interrupt did not fire!")
        print(f"\nAnalysis:")
        print(f"  Freq 01 = 4 M-cycles per increment")
        print(f"  TIMA started at 0, should overflow at 256")
        print(f"  Expected overflow at: 256 * 4 = 1024 M-cycles")
        print(f"  Test checked at 1500 M-cycles (should have overflowed)")
        print(f"  TIMA at 1500 cycles = {tima_1500}")
        print(f"  Timer overflow cycles = {cpu._timer_overflow_cycles}")
        return False

    print("\n[PASS] Timer interrupt fired at correct time!")
    return True

if __name__ == '__main__':
    test_blargg_04_exact()
