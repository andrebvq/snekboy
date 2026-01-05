"""
Test timer initial state and basic HALT behavior
"""

from src.cpu import CPU

def test_timer_initial_values():
    """Check what timer registers are initialized to"""
    cpu = CPU()

    div = cpu.memory.read_byte(0xFF04)
    tima = cpu.memory.read_byte(0xFF05)
    tma = cpu.memory.read_byte(0xFF06)
    tac = cpu.memory.read_byte(0xFF07)

    print("Timer Initial Values:")
    print(f"  DIV  (0xFF04) = 0x{div:02X}")
    print(f"  TIMA (0xFF05) = 0x{tima:02X}")
    print(f"  TMA  (0xFF06) = 0x{tma:02X}")
    print(f"  TAC  (0xFF07) = 0x{tac:02X}")

def test_halt_with_timer():
    """Test that HALT can be exited by timer interrupt"""
    cpu = CPU()

    print("\nHALT with Timer Interrupt Test:")
    print("="*60)

    # Enable timer interrupt in IE
    cpu.memory.write_byte(0xFFFF, 0x04)
    print("Set IE = 0x04 (timer interrupt enabled)")

    # Setup timer to overflow quickly
    cpu.memory.write_byte(0xFF05, 0xFE)  # TIMA = 254
    cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC = enable, freq 01

    # Disable interrupts (IME = 0)
    cpu.ime = False
    print("IME = False (interrupts disabled)")

    # Enter HALT
    cpu.halted = True
    print("CPU halted")

    print(f"\nBefore timer update:")
    print(f"  TIMA = 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"  IF = 0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  Halted = {cpu.halted}")

    # Run enough cycles for timer to overflow
    # With freq 01 (4 M-cycles), need 2*4 = 8 cycles to go from 0xFE to overflow
    for i in range(20):
        cycles_before = cpu.total_cycles
        cpu.step()  # This should update timers and check for wake
        cycles_after = cpu.total_cycles

        tima = cpu.memory.read_byte(0xFF05)
        if_val = cpu.memory.read_byte(0xFF0F)

        if if_val & 0x04:
            print(f"\nAfter {i+1} steps (cycle {cycles_after}):")
            print(f"  TIMA = 0x{tima:02X}")
            print(f"  IF = 0x{if_val:02X} (timer bit SET)")
            print(f"  Halted = {cpu.halted}")

            if not cpu.halted:
                print("  [PASS] CPU woke from HALT due to pending interrupt")
                return True
            break

    if cpu.halted:
        print("  [FAIL] CPU still halted after timer interrupt")
        return False

if __name__ == '__main__':
    print("="*60)
    print("TIMER INITIAL STATE AND HALT TESTS")
    print("="*60)

    test_timer_initial_values()
    test_halt_with_timer()
