"""Each dedicated handler (src/fast_ops.py) must do exactly what the generic
handler does: same registers, flags, memory, bus timing and returned cycles."""
import random
from src.cpu import CPU
from src.memory import Memory


def _cpu():
    mem = Memory()
    mem.load_rom(bytes(0x8000))
    cpu = CPU(mem)
    cpu.simulate_boot()
    return cpu


def _randomise(cpu, rng):
    r = cpu.registers
    r._a, r._b, r._c, r._d, r._e, r._l = (rng.randrange(256) for _ in range(6))
    r._c = rng.choice([r._c, 0x80 + rng.randrange(0x7F)])   # (C) ops: HRAM
    r._h = rng.randrange(0xC0, 0xE0)                         # (HL) in work RAM
    r._sp = rng.randrange(0xC100, 0xDF00)
    r._pc = rng.randrange(0x10000)
    r.flags.f = rng.randrange(16) << 4
    d = cpu.memory._data
    for a in list(range(0xC000, 0xE000, 7)) + list(range(0xFF80, 0xFFFF)):
        d[a] = rng.randrange(256)
    d[(r._h << 8) | r._l] = rng.randrange(256)


def _state(cpu, ret):
    r = cpu.registers
    d = cpu.memory._data
    return (ret, r._a, r._b, r._c, r._d, r._e, r._h, r._l, r._sp, r._pc, r.flags.f,
            cpu._acc, bytes(d[0xC000:0xE000]), bytes(d[0xFF80:0x10000]))


def _operands(rng, opcode, cb):
    if cb:
        return None
    if opcode in (0xE0, 0xF0):
        return 0x80 + rng.randrange(0x7F)                    # LDH: HRAM
    return rng.randrange(0x10000) if opcode in (0xC2, 0xC3, 0xC4, 0xCA, 0xCC, 0xCD, 0xD2, 0xD4, 0xDA, 0xDC) \
        else rng.randrange(256)


def _copy(src, dst):
    a, b = src.registers, dst.registers
    for k in ('_a', '_b', '_c', '_d', '_e', '_h', '_l', '_sp', '_pc'):
        setattr(b, k, getattr(a, k))
    b.flags.f = a.flags.f
    dst.memory._data[:] = src.memory._data


def _check(table, generic, cb, cases=40):
    """Run every dedicated handler and its generic one from identical random
    states; returns how many opcodes were compared."""
    rng = random.Random(7)
    fast_cpu, slow_cpu = _cpu(), _cpu()
    fast, slow = getattr(fast_cpu, table), getattr(slow_cpu, generic)
    checked = 0
    for op in range(256):
        if fast[op] is None or fast[op][0] is slow[op][0]:
            continue                                         # no dedicated handler
        checked += 1
        for _ in range(cases):
            _randomise(fast_cpu, rng)
            _copy(fast_cpu, slow_cpu)
            value = _operands(rng, op, cb)
            results = []
            for cpu, entry in ((fast_cpu, fast[op]), (slow_cpu, slow[op])):
                fn, target, imm = entry[0], entry[1], entry[2]
                if not cb and entry[4] == 1:
                    target = value
                elif not cb and entry[4] == 2:
                    imm = value
                cpu._acc = cpu._synced = 0
                results.append(_state(cpu, fn(target, imm)))
            assert results[0] == results[1], f"{'CB ' if cb else ''}{op:#04x}"
    return checked


def test_fast_handlers_match_generic():
    assert _check('_ops', '_generic_ops', cb=False) > 150


def test_fast_cb_handlers_match_generic():
    assert _check('_cb_ops', '_generic_cb_ops', cb=True) == 256
