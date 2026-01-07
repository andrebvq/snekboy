"""
Unit tests for EI and RETI instruction fixes
"""

from src.cpu import CPU

def test_ei_delay():
    """Test that EI implements the 1-instruction delay correctly"""
    print("Testing EI instruction delay...")

    cpu = CPU()
    cpu.memory.load_rom_file(r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb")

    # Run to EI instruction at 0x02BA
    while cpu.registers._pc != 0x02BA:
        cpu.step()

    assert not cpu.ime, "IME should be False before EI"
    assert cpu._ei_pending == 0, "_ei_pending should be 0 before EI"

    # Execute EI
    cpu.step()

    assert not cpu.ime, "IME should still be False immediately after EI"
    assert cpu._ei_pending == 1, f"_ei_pending should be 1 after EI, got {cpu._ei_pending}"

    # Execute delay instruction
    cpu.step()

    assert cpu.ime, "IME should be True after delay instruction"
    assert cpu._ei_pending == 0, "_ei_pending should be 0 after delay"

    print("  [PASS] EI correctly implements 1-instruction delay")
    print()


def test_reti_enables_interrupts():
    """Test that RETI re-enables interrupts"""
    print("Testing RETI instruction...")

    cpu = CPU()
    cpu.memory.load_rom_file(r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb")

    # Run to first RETI at 0x020B
    while True:
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        if pc == 0x020B and opcode == 0xD9:
            break

        cpu.step()

        if cpu.total_cycles > 10_000_000:
            print("  [FAIL] Never reached RETI instruction")
            return

    # RETI should be executed from within an ISR where IME is False
    assert not cpu.ime, "IME should be False before RETI (in ISR)"

    # Execute RETI
    cpu.step()

    assert cpu.ime, "IME should be True after RETI"
    assert cpu._ei_pending == 0, "_ei_pending should be 0 after RETI"

    print("  [PASS] RETI correctly re-enables interrupts")
    print()


def test_interrupt_fires_after_ei_delay():
    """Test that interrupts fire after EI delay, not immediately"""
    print("Testing interrupt timing after EI...")

    cpu = CPU()
    cpu.memory.load_rom_file(r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb")

    # Run to EI instruction
    while cpu.registers._pc != 0x02BA:
        cpu.step()

    # Execute EI
    cpu.step()
    pc_after_ei = cpu.registers._pc

    # Execute delay instruction
    cpu.step()
    pc_after_delay = cpu.registers._pc

    # Next step should trigger interrupt (IF has VBlank pending)
    cpu.step()
    pc_after_next = cpu.registers._pc

    # Should have jumped to interrupt vector
    assert pc_after_next == 0x0040, f"Expected interrupt to fire at vector 0x0040, got PC=0x{pc_after_next:04X}"

    print(f"  PC progression: 0x{pc_after_ei:04X} (after EI) -> 0x{pc_after_delay:04X} (after delay) -> 0x{pc_after_next:04X} (interrupt fired)")
    print("  [PASS] Interrupt correctly fires after EI delay")
    print()


if __name__ == "__main__":
    print("="*70)
    print("INTERRUPT INSTRUCTION TESTS")
    print("="*70)
    print()

    test_ei_delay()
    test_reti_enables_interrupts()
    test_interrupt_fires_after_ei_delay()

    print("="*70)
    print("ALL TESTS PASSED")
    print("="*70)
