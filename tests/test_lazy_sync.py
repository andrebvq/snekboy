"""Lazy timer/PPU sync in the frame runner must give exactly the same run as
syncing after every instruction: same registers and cycle count after each
instruction, same timer/PPU state at the end of each run."""
import random
from src.cpu import CPU
from src.memory import Memory

IO_READS = [0x41, 0x44, 0x04, 0x05, 0x0F, 0x40]               # STAT LY DIV TIMA IF LCDC
IO_WRITES = [0x07, 0x45, 0x41, 0xFF, 0x0F, 0x05, 0x06, 0x04, 0x40]


def _program(rng):
    """Random straight-line code over the timer/LCD registers, looping back."""
    code = [0xFB]                                               # EI
    for _ in range(rng.randrange(20, 60)):
        kind = rng.random()
        if kind < 0.15:
            code += [0xF0, rng.choice(IO_READS)]                # LDH A,(reg)
        elif kind < 0.4:
            reg = rng.choice(IO_WRITES)
            if reg == 0x40:
                value = rng.choice([0x91, 0x91, 0x11])          # LCD on / off
            elif reg == 0x07:
                value = rng.choice([0x00, 0x04, 0x05, 0x06, 0x07])
            elif reg == 0xFF:
                value = rng.choice([0x1F, 0x1F, 0x04, 0x02, 0x01, rng.randrange(0x20)])
            elif reg == 0x41:
                value = rng.choice([0x08, 0x10, 0x20, 0x40, 0x48, 0x78])
            else:
                value = rng.randrange(256)
            code += [0x3E, value, 0xE0, reg]                    # LD A,n; LDH (reg),A
        elif kind < 0.75:
            # Counted delay loop with no I/O: LD B,n; DEC B; JR NZ,-3.
            # Long stretches like this are where syncing is deferred.
            code += [0x06, rng.randrange(1, 256), 0x05, 0x20, 0xFD]
        elif kind < 0.8:
            code += [0x76]                                      # HALT
        elif kind < 0.85:
            code += [0xF3 if rng.random() < 0.2 else 0xFB]      # DI / EI
        else:
            code += [rng.choice([0x00, 0x04, 0x0C, 0x3C, 0x05, 0x80, 0xA8, 0x47])]
    code += [0xC3, 0x50, 0x01]                                  # JP 0x0150
    return code


def _cpu(seed):
    rng = random.Random(seed)
    rom = bytearray(0x8000)
    for vec in (0x40, 0x48, 0x50, 0x58, 0x60):
        rom[vec] = 0xD9                                         # RETI
    code = _program(rng)
    rom[0x0150:0x0150 + len(code)] = bytes(code)
    mem = Memory()
    mem.load_rom(bytes(rom))
    cpu = CPU(mem)
    cpu.simulate_boot()
    cpu.registers._pc = 0x0150
    cpu.registers._sp = 0xDFF0
    return cpu


def _regs(cpu):
    r = cpu.registers
    return (cpu.total_cycles, r._pc, r._a, r.flags.f, r._b, r._c, r._sp, cpu.ime, cpu.halted)


def _world(cpu):
    d = cpu.memory._data
    p = cpu.ppu
    return (cpu._system_counter, cpu._timer_overflow_cycles, cpu._tima_reloaded,
            bytes(d[0xFF00:0xFF50]), d[0xFFFF], p.cycle_counter, p.ly, p._phase,
            p.oam_locked, p.vram_locked, bytes(bytearray(v for row in p.get_screen_buffer() for v in row)))


def _run(seed, lazy):
    cpu = _cpu(seed)
    log, worlds = [], []
    step = cpu.step
    def logged(*a):
        log.append(_regs(cpu))
        return step(*a)
    cpu.step = logged
    rng = random.Random(seed + 1)
    end = cpu.total_cycles
    for _ in range(12):
        end += rng.choice([70224, 456, 1200, 20000])
        if lazy:
            cpu.run_until_cycle(end)
        else:
            while cpu.total_cycles < end:
                cpu.step(end)                                   # same HALT skip, eager sync
        worlds.append(_world(cpu))
    return log, worlds


def test_lazy_sync_matches_eager_on_random_io_programs():
    deferred = 0
    for seed in range(40):
        lazy_log, lazy_world = _run(seed, True)
        eager_log, eager_world = _run(seed, False)
        assert lazy_log == eager_log, seed
        assert lazy_world == eager_world, seed
        deferred += len(lazy_log)
    assert deferred > 10000


def test_lazy_sync_actually_defers():
    cpu = _cpu(3)
    calls = [0]
    advance = cpu._advance
    def counted(t):
        calls[0] += 1
        return advance(t)
    cpu._advance = counted
    steps = [0]
    step = cpu.step
    def counted_step(*a):
        steps[0] += 1
        return step(*a)
    cpu.step = counted_step
    cpu.run_until_cycle(cpu.total_cycles + 10 * 70224)
    assert calls[0] < steps[0]                                  # fewer syncs than instructions


def test_budget_is_dropped_after_any_advance_outside_instructions():
    """Halted, stopped and locked stretches move the timer/PPU without the
    budget bookkeeping, so the next instruction must recompute it."""
    cpu = _cpu(0)
    cpu.halted = True
    cpu._lazy, cpu._lag, cpu._budget = True, 0, 10_000
    cpu.memory.write_byte(0xFFFF, 0)                            # stays halted
    cpu.step(cpu.total_cycles + 400)
    assert cpu._budget == 0
    cpu.halted, cpu.locked, cpu._budget = False, True, 10_000
    cpu.step()
    assert cpu._budget == 0
