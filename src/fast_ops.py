"""Dedicated handlers for the most frequent instructions.

The generic handlers in instructions_impl.py receive operand names as text
('B', '(HL)', 'NZ') and work out what they mean on every call. Here one small
function per opcode is generated from a template with the register, memory
operand or condition written in, and the flags computed as one byte.

Every function must behave exactly like the generic handler it replaces
(registers, flags, memory accesses and their timing, returned cycles);
tests/test_fast_ops.py checks each one against the generic handler on random
states. Handlers keep the table signature fn(target, immediate): the operand
fetched by step() arrives in the same slot as before.
"""

# Operand index used by the opcode encoding: B C D E H L (HL) A
_REGS = ['_b', '_c', '_d', '_e', '_h', '_l', None, '_a']
_HL = '((r._h << 8) | r._l)'

# Condition codes as expressions on the flag byte
_CONDS = {'NZ': 'not fl.f & 0x80', 'Z': 'fl.f & 0x80',
          'NC': 'not fl.f & 0x10', 'C': 'fl.f & 0x10'}
_COND_BITS = ['NZ', 'Z', 'NC', 'C']      # encoding order in bits 3-4


def _load(i):
    """Expression reading operand i (register or byte at HL)."""
    return f'r.{_REGS[i]}' if _REGS[i] else f'read({_HL})'


def _store(i, expr):
    """Statement writing expr to operand i."""
    return f'r.{_REGS[i]} = {expr}' if _REGS[i] else f'write({_HL}, {expr})'


# --- 8-bit arithmetic / logic on A: body uses v (operand) and a (old A) -----
_ALU = {
    'ADD': ('res = a + v\n'
            'fl.f = (0 if res & 0xFF else 0x80) | (0x20 if (a & 0xF) + (v & 0xF) > 0xF else 0)'
            ' | (0x10 if res > 0xFF else 0)\n'
            'r._a = res & 0xFF'),
    'ADC': ('c = (fl.f >> 4) & 1\n'
            'res = a + v + c\n'
            'fl.f = (0 if res & 0xFF else 0x80) | (0x20 if (a & 0xF) + (v & 0xF) + c > 0xF else 0)'
            ' | (0x10 if res > 0xFF else 0)\n'
            'r._a = res & 0xFF'),
    'SUB': ('res = a - v\n'
            'fl.f = (0 if res & 0xFF else 0x80) | 0x40 | (0x20 if (a & 0xF) < (v & 0xF) else 0)'
            ' | (0x10 if res < 0 else 0)\n'
            'r._a = res & 0xFF'),
    'SBC': ('c = (fl.f >> 4) & 1\n'
            'res = a - v - c\n'
            'fl.f = (0 if res & 0xFF else 0x80) | 0x40 | (0x20 if (a & 0xF) - (v & 0xF) - c < 0 else 0)'
            ' | (0x10 if res < 0 else 0)\n'
            'r._a = res & 0xFF'),
    'AND': ('res = a & v\n'
            'r._a = res\n'
            'fl.f = 0xA0 if res == 0 else 0x20'),
    'XOR': ('res = a ^ v\n'
            'r._a = res\n'
            'fl.f = 0 if res else 0x80'),
    'OR':  ('res = a | v\n'
            'r._a = res\n'
            'fl.f = 0 if res else 0x80'),
    'CP':  ('res = a - v\n'
            'fl.f = (0 if res & 0xFF else 0x80) | 0x40 | (0x20 if (a & 0xF) < (v & 0xF) else 0)'
            ' | (0x10 if res < 0 else 0)'),
}
_ALU_ORDER = ['ADD', 'ADC', 'SUB', 'SBC', 'AND', 'XOR', 'OR', 'CP']

# --- CB rotates / shifts: body uses v, sets res and fl.f ----------------------
_SHIFTS = [
    ('RLC', 'c = v >> 7\nres = ((v << 1) | c) & 0xFF'),
    ('RRC', 'c = v & 1\nres = (v >> 1) | (c << 7)'),
    ('RL',  'c = v >> 7\nres = ((v << 1) | ((fl.f >> 4) & 1)) & 0xFF'),
    ('RR',  'c = v & 1\nres = (v >> 1) | (((fl.f >> 4) & 1) << 7)'),
    ('SLA', 'c = v >> 7\nres = (v << 1) & 0xFF'),
    ('SRA', 'c = v & 1\nres = (v >> 1) | (v & 0x80)'),
    ('SWAP', 'c = 0\nres = ((v & 0x0F) << 4) | (v >> 4)'),
    ('SRL', 'c = v & 1\nres = v >> 1'),
]

_POP_PC = ('sp = r._sp\n'
           'low = read(sp)\n'
           'sp = (sp + 1) & 0xFFFF\n'
           'high = read(sp)\n'
           'r._sp = (sp + 1) & 0xFFFF\n'
           'r._pc = (high << 8) | low')


def _sources():
    """Yield (table, opcode, name, body) for every generated handler.
    table is 'op' or 'cb'; body is the function body (indented later)."""
    # LD r,r' (0x40-0x7F, 0x76 is HALT)
    for op in range(0x40, 0x80):
        if op == 0x76:
            continue
        dst, src = (op >> 3) & 7, op & 7
        yield 'op', op, f'ld_{op:02x}', _store(dst, _load(src))
    # LD r,n: the byte arrives as the immediate
    for i in range(8):
        op = 0x06 | (i << 3)
        yield 'op', op, f'ld_n_{op:02x}', _store(i, 'imm')
    # ALU A,r and ALU A,n
    for k, name in enumerate(_ALU_ORDER):
        for i in range(8):
            op = 0x80 | (k << 3) | i
            yield 'op', op, f'{name.lower()}_{op:02x}', f'v = {_load(i)}\na = r._a\n{_ALU[name]}'
        op = 0xC6 | (k << 3)
        yield 'op', op, f'{name.lower()}_n_{op:02x}', f'v = imm\na = r._a\n{_ALU[name]}'
    # INC r / DEC r: carry kept
    for i in range(8):
        op = 0x04 | (i << 3)
        yield 'op', op, f'inc_{op:02x}', (
            f'v = {_load(i)}\nres = (v + 1) & 0xFF\n'
            'fl.f = (fl.f & 0x10) | (0 if res else 0x80) | (0x20 if (v & 0xF) == 0xF else 0)\n'
            + _store(i, 'res'))
        op = 0x05 | (i << 3)
        yield 'op', op, f'dec_{op:02x}', (
            f'v = {_load(i)}\nres = (v - 1) & 0xFF\n'
            'fl.f = (fl.f & 0x10) | (0 if res else 0x80) | 0x40 | (0x20 if (v & 0xF) == 0 else 0)\n'
            + _store(i, 'res'))
    # JR e / JR cc,e: offset arrives as the target
    jr = ('off = target - 256 if target > 127 else target\n'
          'r._pc = (r._pc + off) & 0xFFFF\n')
    yield 'op', 0x18, 'jr', jr + 'return 12'
    for k, cc in enumerate(_COND_BITS):
        yield 'op', 0x20 | (k << 3), f'jr_{cc.lower()}', (
            f'if {_CONDS[cc]}:\n' + _indent(jr + 'return 12') + '\nreturn 8')
    # JP nn / JP cc,nn
    yield 'op', 0xC3, 'jp', 'r._pc = target & 0xFFFF\nreturn 16'
    for k, cc in enumerate(_COND_BITS):
        yield 'op', 0xC2 | (k << 3), f'jp_{cc.lower()}', (
            f'if {_CONDS[cc]}:\n    r._pc = target & 0xFFFF\n    return 16\nreturn 12')
    # CALL nn / CALL cc,nn: one internal cycle, then push PC
    call = ('cpu._acc += 4\n'
            'pc = r._pc\n'
            'sp = (r._sp - 1) & 0xFFFF\n'
            'r._sp = sp\n'
            'write(sp, (pc >> 8) & 0xFF)\n'
            'sp = (sp - 1) & 0xFFFF\n'
            'r._sp = sp\n'
            'write(sp, pc & 0xFF)\n'
            'r._pc = target & 0xFFFF\n'
            'return 24')
    yield 'op', 0xCD, 'call', call
    for k, cc in enumerate(_COND_BITS):
        yield 'op', 0xC4 | (k << 3), f'call_{cc.lower()}', (
            f'if {_CONDS[cc]}:\n' + _indent(call) + '\nreturn 12')
    # RET / RET cc: the condition costs one internal cycle
    yield 'op', 0xC9, 'ret', _POP_PC + '\nreturn 16'
    for k, cc in enumerate(_COND_BITS):
        yield 'op', 0xC0 | (k << 3), f'ret_{cc.lower()}', (
            f'cpu._acc += 4\nif {_CONDS[cc]}:\n' + _indent(_POP_PC + '\nreturn 20') + '\nreturn 8')
    # LDH (n),A / LDH A,(n) / LDH (C),A / LDH A,(C)
    yield 'op', 0xE0, 'ldh_n_a', 'write(0xFF00 + imm, r._a)'
    yield 'op', 0xF0, 'ldh_a_n', 'r._a = read(0xFF00 + target)'
    yield 'op', 0xE2, 'ldh_c_a', 'write(0xFF00 + r._c, r._a)'
    yield 'op', 0xF2, 'ldh_a_c', 'r._a = read(0xFF00 + r._c)'
    # CB: rotates/shifts, BIT, RES, SET
    for k, (name, rot) in enumerate(_SHIFTS):
        for i in range(8):
            cb = (k << 3) | i
            yield 'cb', cb, f'{name.lower()}_{cb:02x}', (
                f'v = {_load(i)}\n{rot}\n'
                'fl.f = (0 if res else 0x80) | (0x10 if c else 0)\n' + _store(i, 'res'))
    for b in range(8):
        for i in range(8):
            yield 'cb', 0x40 | (b << 3) | i, f'bit{b}_{i}', (
                f'fl.f = (fl.f & 0x10) | 0x20 | (0 if {_load(i)} & {1 << b:#04x} else 0x80)')
            yield 'cb', 0x80 | (b << 3) | i, f'res{b}_{i}', _store(i, f'{_load(i)} & {0xFF ^ (1 << b):#04x}')
            yield 'cb', 0xC0 | (b << 3) | i, f'set{b}_{i}', _store(i, f'{_load(i)} | {1 << b:#04x}')


def _indent(body):
    return '\n'.join('    ' + line for line in body.split('\n'))


def build(cpu):
    """Return ({opcode: fn}, {cb_opcode: fn}) bound to this CPU."""
    ns = {'cpu': cpu, 'r': cpu.registers, 'fl': cpu.registers.flags,
          'read': cpu._read, 'write': cpu._write}
    code = []
    entries = []
    for table, op, name, body in _sources():
        code.append(f'def {name}(target, imm):\n{_indent(body)}\n')
        entries.append((table, op, name))
    exec(compile('\n'.join(code), '<fast_ops>', 'exec'), ns)
    ops, cb_ops = {}, {}
    for table, op, name in entries:
        (ops if table == 'op' else cb_ops)[op] = ns[name]
    return ops, cb_ops
