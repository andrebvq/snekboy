"""
Test TAC write obscure behavior
"""

from src.cpu import CPU

def test_tac_write_spurious_tick():
    """
    Test that writing to TAC can trigger spurious timer ticks
    """
    print("=" * 60)
    print("TAC Write Obscure Behavior Test")
    print("=" * 60)

    cpu = CPU()

    # Setup: Set system counter to a value where bit 3 is set
    # Bit 3 is used for frequency 01 (4 M-cycles)
    # Let's set counter to 0x0008 (bit 3 = 1)
    cpu._system_counter = 0x0008
    print(f"System counter: 0x{cpu._system_counter:04X} (bit 3 = 1)")

    # Set TIMA to a known value
    cpu.memory.write_byte(0xFF05, 0xFE)  # Close to overflow
    print(f"TIMA before: 0x{cpu.memory.read_byte(0xFF05):02X}")

    # TAC is currently disabled (default 0x00)
    print(f"TAC before: 0x{cpu.memory.read_byte(0xFF07):02X}")

    # Write TAC = 0x05 (enable, frequency 01)
    # This selects bit 3, which is currently 1
    # Going from disabled to enabled with bit 3=1 should trigger a tick on DMG
    print("\nWriting TAC = 0x05 (enable, freq 01)...")
    cpu.memory.write_byte(0xFF07, 0x05)

    tima_after = cpu.memory.read_byte(0xFF05)
    print(f"TIMA after: 0x{tima_after:02X}")

    if tima_after == 0xFF:
        print("[PASS] Spurious tick occurred (0xFE -> 0xFF)")
        return True
    elif tima_after == 0xFE:
        print("[FAIL] No spurious tick occurred")
        return False
    else:
        print(f"[UNEXPECTED] TIMA = 0x{tima_after:02X}")
        return False

def test_tac_frequency_change_tick():
    """
    Test that changing TAC frequency can trigger spurious ticks
    """
    print("\n" + "=" * 60)
    print("TAC Frequency Change Test")
    print("=" * 60)

    cpu = CPU()

    # Set system counter so bit 9 is set but bit 3 is clear
    # Bit 9 = 512 (0x200), bit 3 = 8 (0x008)
    cpu._system_counter = 0x0200  # bit 9 = 1, bit 3 = 0
    print(f"System counter: 0x{cpu._system_counter:04X}")
    print(f"  Bit 9 (freq 00): {(cpu._system_counter >> 9) & 1}")
    print(f"  Bit 3 (freq 01): {(cpu._system_counter >> 3) & 1}")

    # Enable timer with frequency 00 (bit 9)
    cpu.memory.write_byte(0xFF07, 0x04)
    cpu.memory.write_byte(0xFF05, 0xFE)
    print(f"\nTAC = 0x04 (enable, freq 00 - monitoring bit 9)")
    print(f"TIMA = 0x{cpu.memory.read_byte(0xFF05):02X}")

    # Change to frequency 01 (bit 3)
    # Going from bit 9 (set) to bit 3 (unset) should trigger tick
    print("\nChanging to TAC = 0x05 (freq 01 - monitoring bit 3)...")
    cpu.memory.write_byte(0xFF07, 0x05)

    tima_after = cpu.memory.read_byte(0xFF05)
    print(f"TIMA after: 0x{tima_after:02X}")

    if tima_after == 0xFF:
        print("[PASS] Spurious tick on frequency change (bit 9=1 -> bit 3=0)")
        return True
    else:
        print(f"[FAIL] Expected 0xFF, got 0x{tima_after:02X}")
        return False

if __name__ == '__main__':
    test_tac_write_spurious_tick()
    test_tac_frequency_change_tick()
