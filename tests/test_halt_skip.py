"""HALT skip-ahead: a halted CPU that jumps to the next event must end up in
exactly the state it reaches when idling one M-cycle per step."""
import random
from src.cpu import CPU
from src.memory import Memory

# HALT; INC B; JR -3 (back to HALT): wakes, counts, halts again (IME off)
PROGRAM = [0x76, 0x04, 0x18, 0xFC]


def _cpu(seed):
    rng = random.Random(seed)
    rom = bytearray(0x8000)
    rom[0x0150:0x0150 + len(PROGRAM)] = bytes(PROGRAM)
    mem = Memory()
    mem.load_rom(bytes(rom))
    cpu = CPU(mem)
    cpu.simulate_boot()
    cpu.registers._pc = 0x0150
    cpu.ime = False
    w = mem.write_byte
    w(0xFF07, rng.choice([0x00, 0x04, 0x05, 0x06, 0x07]))      # timer off / each rate
    w(0xFF05, rng.randrange(256))
    w(0xFF06, rng.randrange(256))
    w(0xFF45, rng.randrange(154))                              # LYC
    w(0xFF41, rng.choice([0x00, 0x08, 0x10, 0x20, 0x40, 0x48, 0x60]))
    if rng.random() < 0.2:
        w(0xFF40, 0x00)                                        # LCD off: only the timer
    w(0xFFFF, rng.choice([0x01, 0x02, 0x04, 0x03, 0x07, 0x00]))
    for _ in range(rng.randrange(0, 2000)):                    # random start point
        cpu.step()
    return cpu


def _state(cpu):
    r = cpu.registers
    d = cpu.memory._data
    return (cpu.total_cycles, r._pc, r._b, cpu.halted, cpu._system_counter,
            d[0xFF04], d[0xFF05], d[0xFF0F], d[0xFF41], d[0xFF44],
            cpu.ppu.cycle_counter, cpu.ppu.ly, cpu.ppu._phase)


def test_halt_skip_matches_single_steps():
    skipped = 0
    for seed in range(60):
        fast, slow = _cpu(seed), _cpu(seed)
        end = fast.total_cycles
        for _ in range(8):                                     # 8 "frames" of mixed lengths
            end += random.Random(seed * 31 + _).choice([70224, 4560, 456, 1000])
            calls = 0
            while fast.total_cycles < end:
                fast.step(end)
                calls += 1
            while slow.total_cycles < end:
                slow.step()
                skipped += 1
            skipped -= calls
            assert _state(fast) == _state(slow), seed
    assert skipped > 0                                         # the skip actually happened
