"""
Test the timer implementation
"""

from src.cpu import CPU

def test_div_register():
    """Test DIV register increments every 256 cycles"""
    cpu = CPU()

    print("Testing DIV register...")
    print("="*80)

    # DIV should increment every 256 cycles (64 M-cycles)
    initial_div = cpu.memory.read_byte(0xFF04)
    print(f"Initial DIV: 0x{initial_div:02X}")

    # Run for 256 T-cycles (should increment DIV once)
    for _ in range(64):  # 64 M-cycles = 256 T-cycles
        cpu.step()  # NOP takes 1 M-cycle

    div_after_256 = cpu.memory.read_byte(0xFF04)
    print(f"DIV after 256 cycles: 0x{div_after_256:02X}")

    if div_after_256 == (initial_div + 1) & 0xFF:
        print("[PASS] DIV incremented correctly")
    else:
        print(f"[FAIL] Expected DIV={initial_div + 1}, got {div_after_256}")

    print()

def test_timer_basic():
    """Test TIMA with basic configuration"""
    cpu = CPU()

    print("Testing TIMA basic operation...")
    print("="*80)

    # Configure timer:
    # - TMA = 0x00 (reload value)
    # - TAC = 0x05 (enabled, 262144 Hz = every 16 cycles)
    cpu.memory.write_byte(0xFF06, 0x00)  # TMA
    cpu.memory.write_byte(0xFF05, 0xF0)  # TIMA starting value
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC: enable + 262144 Hz

    tima_before = cpu.memory.read_byte(0xFF05)
    print(f"TIMA before: 0x{tima_before:02X}")
    print(f"TAC: 0x{cpu.memory.read_byte(0xFF07):02X}")

    # Run for 16 T-cycles (4 M-cycles) - should increment TIMA once
    for _ in range(4):
        cpu.step()

    tima_after = cpu.memory.read_byte(0xFF05)
    print(f"TIMA after 16 cycles: 0x{tima_after:02X}")

    if tima_after == (tima_before + 1) & 0xFF:
        print("[PASS] TIMA incremented correctly")
    else:
        print(f"[FAIL] Expected TIMA={tima_before + 1}, got {tima_after}")

    print()

def test_timer_overflow():
    """Test TIMA overflow and reload from TMA"""
    cpu = CPU()

    print("Testing TIMA overflow and TMA reload...")
    print("="*80)

    # Configure timer:
    # - TMA = 0xF0 (reload value)
    # - TIMA = 0xFE (close to overflow)
    # - TAC = 0x05 (enabled, 262144 Hz)
    cpu.memory.write_byte(0xFF06, 0xF0)  # TMA
    cpu.memory.write_byte(0xFF05, 0xFE)  # TIMA
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC

    print(f"TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"TMA: 0x{cpu.memory.read_byte(0xFF06):02X}")

    # Increment once: 0xFE -> 0xFF
    for _ in range(4):
        cpu.step()

    tima = cpu.memory.read_byte(0xFF05)
    print(f"TIMA after 1 increment: 0x{tima:02X}")

    # Increment again: 0xFF -> 0x00 -> reload from TMA (0xF0)
    for _ in range(4):
        cpu.step()

    # Need a few more cycles for reload delay
    for _ in range(4):
        cpu.step()

    tima = cpu.memory.read_byte(0xFF05)
    if_reg = cpu.memory.read_byte(0xFF0F)

    print(f"TIMA after overflow: 0x{tima:02X}")
    print(f"IF register: 0x{if_reg:02X} (bit 2 = timer interrupt)")

    if tima == 0xF0:
        print("[PASS] TIMA reloaded from TMA correctly")
    else:
        print(f"[FAIL] Expected TIMA=0xF0, got 0x{tima:02X}")

    if (if_reg & 0x04) != 0:
        print("[PASS] Timer interrupt flag set")
    else:
        print("[FAIL] Timer interrupt flag not set")

    print()

def test_timer_frequencies():
    """Test all 4 timer frequencies"""
    cpu = CPU()

    print("Testing all timer frequencies...")
    print("="*80)

    frequencies = {
        0: (1024, "4096 Hz"),
        1: (16, "262144 Hz"),
        2: (64, "65536 Hz"),
        3: (256, "16384 Hz"),
    }

    for freq_select, (cycles, name) in frequencies.items():
        cpu = CPU()  # Fresh CPU for each test

        # Configure timer
        cpu.memory.write_byte(0xFF06, 0x00)  # TMA
        cpu.memory.write_byte(0xFF05, 0x00)  # TIMA
        cpu.memory.write_byte(0xFF07, 0x04 | freq_select)  # TAC: enable + frequency

        # Run for the specified number of cycles
        m_cycles = cycles // 4
        for _ in range(m_cycles):
            cpu.step()

        tima = cpu.memory.read_byte(0xFF05)

        if tima == 1:
            print(f"[PASS] Frequency {freq_select} ({name}): TIMA incremented after {cycles} cycles")
        else:
            print(f"[FAIL] Frequency {freq_select} ({name}): Expected TIMA=1, got {tima}")

    print()

if __name__ == '__main__':
    test_div_register()
    test_timer_basic()
    test_timer_overflow()
    test_timer_frequencies()

    print("="*80)
    print("Timer tests complete!")
