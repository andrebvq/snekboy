"""Interrupt and timer edge cases, checked against Pan Docs ("Interrupts", "HALT",
"Timer obscure behaviour") and the mooneye tests named in each docstring."""

from src.cpu import CPU
from src.memory import Memory

SERIAL = 0x08          # IE/IF bit 3, vector 0x0058
TIMER = 0x04           # IE/IF bit 2, vector 0x0050


def _cpu(program, start=0x0100):
    rom = bytearray(0x8000)
    rom[start:start + len(program)] = bytes(program)
    mem = Memory()
    mem.load_rom(bytes(rom))
    cpu = CPU(mem)
    cpu.simulate_boot()
    cpu.registers._pc = start
    cpu.registers._sp = 0xDFFE
    return cpu


def _pending(cpu, bits):
    cpu.memory.write_byte(0xFFFF, bits)
    cpu.memory.write_byte(0xFF0F, bits)


def _pushed_pc(cpu):
    sp = cpu.registers._sp
    return cpu.memory.read_byte(sp) | (cpu.memory.read_byte(sp + 1) << 8)


def test_ei_then_di_lets_no_interrupt_through():
    """rapid_di_ei"""
    cpu = _cpu([0xFB, 0xF3, 0x00, 0x00])        # EI; DI; NOP; NOP
    _pending(cpu, SERIAL)
    for _ in range(4):
        cpu.step()
    assert cpu.registers._pc == 0x0104
    assert not cpu.ime


def test_second_ei_does_not_restart_delay():
    """ei_sequence: the interrupt is taken right after the second EI."""
    cpu = _cpu([0xFB, 0xFB, 0x00])              # EI; EI; NOP
    _pending(cpu, SERIAL)
    cpu.step()
    cpu.step()
    assert cpu.ime
    cpu.step()                                  # dispatch
    assert cpu.registers._pc == 0x0058
    assert _pushed_pc(cpu) == 0x0102


def test_dispatch_cancelled_when_push_overwrites_ie():
    """ie_push: with SP=0x0000 the PC high byte lands in IE (0xFFFF)."""
    cpu = _cpu([0x00], start=0x0000 + 0x0200)   # PC 0x0200: high byte 0x02 -> IE
    cpu.registers._sp = 0x0000
    cpu.ime = True
    _pending(cpu, TIMER)                        # 0x02 written to IE drops the timer bit
    cpu.step()
    assert cpu.registers._pc == 0x0000
    assert cpu.memory.read_byte(0xFF0F) & TIMER # request not acknowledged


def test_dispatch_switches_to_interrupt_still_enabled_after_push():
    cpu = _cpu([0x00], start=0x0200)
    cpu.registers._sp = 0x0000
    cpu.ime = True
    cpu.memory.write_byte(0xFFFF, TIMER)
    cpu.memory.write_byte(0xFF0F, TIMER | 0x02) # STAT also requested; IE becomes 0x02
    cpu.step()
    assert cpu.registers._pc == 0x0048          # STAT vector, not timer
    assert cpu.memory.read_byte(0xFF0F) & 0x1F == TIMER


def test_ei_halt_with_pending_interrupt_returns_to_halt():
    """Pan Docs HALT bug: after EI; HALT the handler returns to the HALT."""
    cpu = _cpu([0xFB, 0x76, 0x00])              # EI; HALT; NOP
    _pending(cpu, SERIAL)
    cpu.step()                                  # EI
    cpu.step()                                  # HALT
    cpu.step()                                  # dispatch
    assert cpu.registers._pc == 0x0058
    assert _pushed_pc(cpu) == 0x0101            # address of the HALT itself
    assert not cpu._halt_bug_active             # handler's first fetch is normal


def _timer_cpu(tac):
    cpu = _cpu([0x00] * 16)
    cpu.memory.write_byte(0xFF05, 0x10)         # TIMA
    cpu.memory.write_byte(0xFF07, tac)
    return cpu


def test_div_write_ticks_tima_when_selected_bit_is_set():
    """tim00..tim11_div_trigger"""
    cpu = _timer_cpu(0x05)                      # enabled, counter bit 3
    cpu._system_counter = 0x0008                # bit 3 set
    cpu.memory.write_byte(0xFF04, 0x00)
    assert cpu.memory.read_byte(0xFF05) == 0x11
    assert cpu._system_counter == 0


def test_div_write_no_tick_when_bit_clear_or_timer_off():
    cpu = _timer_cpu(0x05)
    cpu._system_counter = 0x0004                # bit 3 clear
    cpu.memory.write_byte(0xFF04, 0x00)
    assert cpu.memory.read_byte(0xFF05) == 0x10
    cpu = _timer_cpu(0x01)                      # disabled
    cpu._system_counter = 0x0008
    cpu.memory.write_byte(0xFF04, 0x00)
    assert cpu.memory.read_byte(0xFF05) == 0x10


def _reload_cpu():
    """CPU whose last M-cycle reloaded TIMA from TMA."""
    cpu = _timer_cpu(0x04)                      # enabled, slowest rate: no tick here
    cpu._system_counter = 0
    cpu.memory.write_byte(0xFF06, 0x7F)         # TMA
    cpu.memory._data[0xFF05] = 0x00
    cpu._timer_overflow_cycles = 1
    cpu._update_timers(1)
    assert cpu._tima_reloaded and cpu.memory.read_byte(0xFF05) == 0x7F
    return cpu


def test_tima_write_ignored_on_reload_cycle():
    """tima_write_reloading"""
    cpu = _reload_cpu()
    cpu.memory.write_byte(0xFF05, 0xFE)
    assert cpu.memory.read_byte(0xFF05) == 0x7F


def test_tma_write_on_reload_cycle_also_sets_tima():
    """tma_write_reloading"""
    cpu = _reload_cpu()
    cpu.memory.write_byte(0xFF06, 0x42)
    assert cpu.memory.read_byte(0xFF05) == 0x42


def test_reload_window_is_one_m_cycle():
    cpu = _reload_cpu()
    cpu._update_timers(1)
    assert not cpu._tima_reloaded
    cpu.memory.write_byte(0xFF05, 0xFE)
    assert cpu.memory.read_byte(0xFF05) == 0xFE
