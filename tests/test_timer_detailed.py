"""
Detailed timer testing to find the issue
"""

from src.cpu import CPU

def test_timer_increment_timing():
    """Test exact timing of TIMA increments"""
    print("Testing TIMA increment timing (262144 Hz)...")
    print("="*80)

    cpu = CPU()

    # Configure timer: 262144 Hz (bit 3, every 16 T-cycles)
    cpu.memory.write_byte(0xFF06, 0x00)  # TMA
    cpu.memory.write_byte(0xFF05, 0x00)  # TIMA
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC: enable + freq 1

    print(f"Initial state:")
    print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"  System counter: {cpu._system_counter}")

    # Run exactly 16 T-cycles (4 M-cycles)
    for i in range(4):
        cpu.step()  # Each NOP is 1 M-cycle = 4 T-cycles
        tima = cpu.memory.read_byte(0xFF05)
        print(f"  After {(i+1)*4} T-cycles: TIMA=0x{tima:02X}, sys_counter={cpu._system_counter}")

    tima = cpu.memory.read_byte(0xFF05)
    if tima == 1:
        print("[PASS] TIMA incremented exactly once after 16 T-cycles")
    else:
        print(f"[FAIL] Expected TIMA=1, got {tima}")

    print()

def test_div_timing():
    """Test DIV register timing"""
    print("Testing DIV timing...")
    print("="*80)

    cpu = CPU()

    initial_div = cpu.memory.read_byte(0xFF04)
    print(f"Initial DIV: 0x{initial_div:02X}")
    print(f"Initial system counter: {cpu._system_counter}")

    # Run for 256 T-cycles (64 M-cycles)
    for i in range(64):
        cpu.step()
        if i % 16 == 15:  # Check every 64 T-cycles
            div = cpu.memory.read_byte(0xFF04)
            print(f"  After {(i+1)*4} T-cycles: DIV=0x{div:02X}, sys_counter={cpu._system_counter}")

    div = cpu.memory.read_byte(0xFF04)
    expected = (initial_div + 1) & 0xFF

    if div == expected:
        print(f"[PASS] DIV incremented correctly to 0x{div:02X}")
    else:
        print(f"[FAIL] Expected DIV=0x{expected:02X}, got 0x{div:02X}")

    print()

def test_tma_reload_timing():
    """Test the exact timing of TMA reload"""
    print("Testing TMA reload timing...")
    print("="*80)

    cpu = CPU()

    # Configure timer
    cpu.memory.write_byte(0xFF06, 0xAB)  # TMA = 0xAB
    cpu.memory.write_byte(0xFF05, 0xFF)  # TIMA = 0xFF (about to overflow)
    cpu.memory.write_byte(0xFF07, 0x05)  # TAC: enable + 262144 Hz

    print(f"Initial state:")
    print(f"  TIMA: 0x{cpu.memory.read_byte(0xFF05):02X}")
    print(f"  TMA: 0x{cpu.memory.read_byte(0xFF06):02X}")
    print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")

    # Step through the overflow
    for i in range(8):
        cpu.step()
        tima = cpu.memory.read_byte(0xFF05)
        if_reg = cpu.memory.read_byte(0xFF0F)
        print(f"  After {(i+1)*4} T-cycles: TIMA=0x{tima:02X}, IF=0x{if_reg:02X}")

        if tima == 0xAB:
            print(f"    -> TMA reload occurred after {(i+1)*4} T-cycles")
            if (if_reg & 0x04) != 0:
                print(f"    -> Timer interrupt flag set")
            break

    print()

def test_all_frequencies():
    """Test all 4 timer frequencies in detail"""
    print("Testing all timer frequencies with falling edge detection...")
    print("="*80)

    frequencies = {
        0: (1024, "4096 Hz", 9),      # Bit 9
        1: (16, "262144 Hz", 3),      # Bit 3
        2: (64, "65536 Hz", 5),       # Bit 5
        3: (256, "16384 Hz", 7),      # Bit 7
    }

    for freq_select, (cycles, name, bit_pos) in frequencies.items():
        cpu = CPU()

        print(f"\nFrequency {freq_select} ({name}), monitoring bit {bit_pos}:")

        # Configure timer
        cpu.memory.write_byte(0xFF06, 0x00)  # TMA
        cpu.memory.write_byte(0xFF05, 0x00)  # TIMA
        cpu.memory.write_byte(0xFF07, 0x04 | freq_select)  # TAC

        # Track bit state
        m_cycles_needed = cycles // 4
        bit_values = []

        for i in range(m_cycles_needed + 4):
            prev_counter = cpu._system_counter
            cpu.step()
            curr_counter = cpu._system_counter

            prev_bit = (prev_counter >> bit_pos) & 1
            curr_bit = (curr_counter >> bit_pos) & 1

            if prev_bit != curr_bit:
                bit_values.append((i+1, prev_bit, curr_bit))

        tima = cpu.memory.read_byte(0xFF05)

        print(f"  Bit transitions: {bit_values[:3]}")  # Show first few
        print(f"  TIMA after {cycles} T-cycles: {tima}")

        if tima == 1:
            print(f"  [PASS]")
        else:
            print(f"  [FAIL] Expected TIMA=1, got {tima}")

if __name__ == '__main__':
    test_div_timing()
    test_timer_increment_timing()
    test_tma_reload_timing()
    test_all_frequencies()
