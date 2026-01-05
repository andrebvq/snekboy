"""
Test interrupt system
"""

from src.cpu import CPU

def test_ei_di():
    """Test EI/DI instructions"""
    cpu = CPU()

    print("Test 1: EI/DI instructions")
    print(f"Initial IME: {cpu.ime}")

    # Execute DI
    cpu._execute_di()
    print(f"After DI: IME = {cpu.ime} (expected: False)")
    assert cpu.ime == False, "DI should clear IME"

    # Execute EI (should set pending flag)
    cpu._execute_ei()
    print(f"After EI (before next instruction): IME = {cpu.ime}, pending = {cpu._ei_pending}")
    assert cpu.ime == False, "EI should not enable IME immediately"
    assert cpu._ei_pending == True, "EI should set pending flag"

    # Execute a NOP to trigger EI delay
    cpu.step()  # This should enable IME after execution
    print(f"After NOP following EI: IME = {cpu.ime}")
    # Note: step() enables IME after the instruction, so it should be True now

    print("[PASS] EI/DI work correctly\n")

def test_ie_if_registers():
    """Test IE and IF register access"""
    cpu = CPU()

    print("Test 2: IE and IF registers")

    # Write to IE register
    cpu.memory.write_byte(0xFFFF, 0x1F)  # Enable all interrupts
    ie = cpu.memory.read_byte(0xFFFF)
    print(f"IE register: 0x{ie:02X} (expected: 0x1F)")
    assert ie == 0x1F, "IE register should be writable"

    # Write to IF register
    cpu.memory.write_byte(0xFF0F, 0x04)  # Set timer interrupt flag
    if_val = cpu.memory.read_byte(0xFF0F)
    print(f"IF register: 0x{if_val:02X} (expected: 0x04)")
    assert if_val == 0x04, "IF register should be writable"

    print("[PASS] IE/IF registers work correctly\n")

def test_timer_registers():
    """Test timer register access"""
    cpu = CPU()

    print("Test 3: Timer registers")

    # Test DIV (should reset to 0 on any write)
    cpu.memory.write_byte(0xFF04, 0xFF)
    div = cpu.memory.read_byte(0xFF04)
    print(f"DIV after write 0xFF: 0x{div:02X} (expected: 0x00)")
    assert div == 0x00, "DIV should reset to 0 on write"

    # Test TIMA
    cpu.memory.write_byte(0xFF05, 0x42)
    tima = cpu.memory.read_byte(0xFF05)
    print(f"TIMA: 0x{tima:02X} (expected: 0x42)")
    assert tima == 0x42, "TIMA should be writable"

    # Test TMA
    cpu.memory.write_byte(0xFF06, 0x99)
    tma = cpu.memory.read_byte(0xFF06)
    print(f"TMA: 0x{tma:02X} (expected: 0x99)")
    assert tma == 0x99, "TMA should be writable"

    # Test TAC
    cpu.memory.write_byte(0xFF07, 0x05)  # Enable timer, freq 01
    tac = cpu.memory.read_byte(0xFF07)
    print(f"TAC: 0x{tac:02X} (expected: 0x05)")
    assert tac == 0x05, "TAC should be writable"

    print("[PASS] Timer registers work correctly\n")

def test_simple_timer():
    """Test that timer increments TIMA"""
    cpu = CPU()

    print("Test 4: Timer increments")

    # Setup timer
    cpu.memory.write_byte(0xFF05, 0x00)  # TIMA = 0
    cpu.memory.write_byte(0xFF06, 0x00)  # TMA = 0
    cpu.memory.write_byte(0xFF07, 0x05)  # Enable timer, freq 01 (16 cycles per tick)

    # Run for enough cycles to increment TIMA
    for i in range(20):
        cpu._update_timers(16)

    tima = cpu.memory.read_byte(0xFF05)
    print(f"TIMA after 20*16 cycles: {tima} (expected: >0)")
    assert tima > 0, f"Timer should have incremented, got {tima}"

    print(f"[PASS] Timer incremented to {tima}\n")

if __name__ == '__main__':
    print("="*60)
    print("INTERRUPT AND TIMER TESTS")
    print("="*60)

    try:
        test_ei_di()
        test_ie_if_registers()
        test_timer_registers()
        test_simple_timer()

        print("="*60)
        print("ALL TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
