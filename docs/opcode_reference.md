# Game Boy Opcode Quick Reference

Quick lookup for opcode implementations.

## Control Flow

### JP - Unconditional Jump
```python
0xC3: JP nn      # Jump to 16-bit address
# Implementation:
def _execute_jp(self, address, condition=None):
    self.registers._pc = validate_word(address)
```

### JP cc - Conditional Jump
```python
0xC2: JP NZ,nn   # Jump if Z flag = 0
0xCA: JP Z,nn    # Jump if Z flag = 1
0xD2: JP NC,nn   # Jump if C flag = 0
0xDA: JP C,nn    # Jump if C flag = 1

# Implementation:
def _execute_jp_conditional(self, address, condition):
    should_jump = False
    if condition == 'NZ':
        should_jump = not self.registers.flags.zero
    elif condition == 'Z':
        should_jump = self.registers.flags.zero
    elif condition == 'NC':
        should_jump = not self.registers.flags.carry
    elif condition == 'C':
        should_jump = self.registers.flags.carry

    if should_jump:
        self.registers._pc = validate_word(address)
```

### JR - Relative Jump
```python
0x18: JR n       # Jump relative (signed offset)
0x20: JR NZ,n    # Jump relative if not zero
0x28: JR Z,n     # Jump relative if zero
0x30: JR NC,n    # Jump relative if no carry
0x38: JR C,n     # Jump relative if carry

# Implementation:
def _execute_jr(self, offset, condition=None):
    # offset is signed 8-bit: -128 to +127
    if offset > 127:
        offset = offset - 256  # Convert to signed

    should_jump = True
    if condition == 'NZ':
        should_jump = not self.registers.flags.zero
    elif condition == 'Z':
        should_jump = self.registers.flags.zero
    elif condition == 'NC':
        should_jump = not self.registers.flags.carry
    elif condition == 'C':
        should_jump = self.registers.flags.carry

    if should_jump:
        self.registers._pc = validate_word(self.registers._pc + offset)
```

### CALL - Call Subroutine
```python
0xCD: CALL nn    # Push PC to stack, jump to nn
0xC4: CALL NZ,nn
0xCC: CALL Z,nn
0xD4: CALL NC,nn
0xDC: CALL C,nn

# Implementation:
def _execute_call(self, address, condition=None):
    should_call = True
    if condition == 'NZ':
        should_call = not self.registers.flags.zero
    # ... (same condition logic as JP)

    if should_call:
        # Push current PC onto stack
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, (self.registers._pc >> 8) & 0xFF)
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, self.registers._pc & 0xFF)

        # Jump to address
        self.registers._pc = validate_word(address)
```

### RET - Return from Subroutine
```python
0xC9: RET        # Pop PC from stack
0xC0: RET NZ
0xC8: RET Z
0xD0: RET NC
0xD8: RET C

# Implementation:
def _execute_ret(self, condition=None):
    should_ret = True
    if condition == 'NZ':
        should_ret = not self.registers.flags.zero
    # ... (same condition logic)

    if should_ret:
        # Pop PC from stack
        low = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)
        high = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)

        self.registers._pc = (high << 8) | low
```

---

## Rotate and Shift Instructions

### RLCA - Rotate Left Circular Accumulator
```python
0x07: RLCA
# Rotate A left. Old bit 7 to Carry flag.
def _execute_rlca(self):
    carry_bit = (self.registers._a >> 7) & 1
    self.registers._a = ((self.registers._a << 1) | carry_bit) & 0xFF

    self.registers.flags.zero = False  # RLCA always resets Z
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = False
    self.registers.flags.carry = (carry_bit == 1)
```

### RLA - Rotate Left through carry
```python
0x17: RLA
# Rotate A left through carry
def _execute_rla(self):
    old_carry = 1 if self.registers.flags.carry else 0
    new_carry = (self.registers._a >> 7) & 1

    self.registers._a = ((self.registers._a << 1) | old_carry) & 0xFF

    self.registers.flags.zero = False
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = False
    self.registers.flags.carry = (new_carry == 1)
```

### RRCA - Rotate Right Circular
```python
0x0F: RRCA
def _execute_rrca(self):
    carry_bit = self.registers._a & 1
    self.registers._a = (self.registers._a >> 1) | (carry_bit << 7)

    self.registers.flags.zero = False
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = False
    self.registers.flags.carry = (carry_bit == 1)
```

### RRA - Rotate Right through carry
```python
0x1F: RRA
def _execute_rra(self):
    old_carry = 1 if self.registers.flags.carry else 0
    new_carry = self.registers._a & 1

    self.registers._a = (self.registers._a >> 1) | (old_carry << 7)

    self.registers.flags.zero = False
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = False
    self.registers.flags.carry = (new_carry == 1)
```

---

## 16-bit Arithmetic

### INC rr - Increment 16-bit register
```python
0x03: INC BC
0x13: INC DE
0x23: INC HL
0x33: INC SP

def _execute_inc_16(self, register_pair):
    if register_pair == 'BC':
        self.registers.bc = validate_word(self.registers.bc + 1)
    elif register_pair == 'DE':
        self.registers.de = validate_word(self.registers.de + 1)
    elif register_pair == 'HL':
        self.registers.hl = validate_word(self.registers.hl + 1)
    elif register_pair == 'SP':
        self.registers._sp = validate_word(self.registers._sp + 1)

    # No flags affected!
```

### DEC rr - Decrement 16-bit register
```python
0x0B: DEC BC
0x1B: DEC DE
0x2B: DEC HL
0x3B: DEC SP

# Similar to INC but subtract 1
# No flags affected!
```

### ADD HL,rr - Add to HL
```python
0x09: ADD HL,BC
0x19: ADD HL,DE
0x29: ADD HL,HL   # Double HL
0x39: ADD HL,SP

def _execute_add_hl(self, source):
    hl = self.registers.hl

    if source == 'BC':
        value = self.registers.bc
    elif source == 'DE':
        value = self.registers.de
    elif source == 'HL':
        value = self.registers.hl
    elif source == 'SP':
        value = self.registers._sp

    result = hl + value

    self.registers.hl = validate_word(result)

    # Flags
    # Zero NOT affected
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = ((hl & 0x0FFF) + (value & 0x0FFF)) > 0x0FFF
    self.registers.flags.carry = result > 0xFFFF
```

---

## More LD Variants

### LD (nn),A - Store A at address
```python
0xEA: LD (nn),A   # Store A at 16-bit address

def decode:
    if opcode == 0xEA:
        address = fetch_word_func()
        return (InstructionType.LD, f'({address})', 'A')

def execute:
    # target is like '(0x1234)'
    address = int(target[1:-1], 16)  # Extract address
    self.memory.write_byte(address, self.registers._a)
```

### LD A,(nn) - Load A from address
```python
0xFA: LD A,(nn)   # Load from 16-bit address into A
```

### LDI/LDD - Load with auto increment/decrement
```python
0x22: LDI (HL),A  # Store A at (HL), then HL++
0x2A: LDI A,(HL)  # Load from (HL) into A, then HL++
0x32: LDD (HL),A  # Store A at (HL), then HL--
0x3A: LDD A,(HL)  # Load from (HL) into A, then HL--

def _execute_ldi(self, target, source):
    if target == '(HL)' and source == 'A':
        self.memory.write_byte(self.registers.hl, self.registers._a)
        self.registers.hl = validate_word(self.registers.hl + 1)
    elif target == 'A' and source == '(HL)':
        self.registers._a = self.memory.read_byte(self.registers.hl)
        self.registers.hl = validate_word(self.registers.hl + 1)
```

---

## CB-Prefixed Instructions (BIT operations)

When you see opcode 0xCB, next byte is the actual instruction:

### BIT - Test bit
```python
0xCB 0x40-0x7F: BIT n,r   # Test bit n of register r

def _execute_bit(self, bit_num, register):
    value = self._get_register_value(register)
    bit_set = (value >> bit_num) & 1

    self.registers.flags.zero = (bit_set == 0)
    self.registers.flags.subtract = False
    self.registers.flags.half_carry = True
    # Carry not affected
```

### SET - Set bit
```python
0xCB 0xC0-0xFF: SET n,r   # Set bit n of register r

def _execute_set(self, bit_num, register):
    value = self._get_register_value(register)
    value |= (1 << bit_num)
    self._set_register_value(register, value)
    # No flags affected
```

### RES - Reset bit
```python
0xCB 0x80-0xBF: RES n,r   # Reset bit n of register r

def _execute_res(self, bit_num, register):
    value = self._get_register_value(register)
    value &= ~(1 << bit_num)
    self._set_register_value(register, value)
    # No flags affected
```

---

## Common Patterns

### Check Flag Condition
```python
def check_condition(self, condition):
    if condition == 'NZ':
        return not self.registers.flags.zero
    elif condition == 'Z':
        return self.registers.flags.zero
    elif condition == 'NC':
        return not self.registers.flags.carry
    elif condition == 'C':
        return self.registers.flags.carry
    return True  # No condition
```

### Signed Byte
```python
def to_signed(value):
    """Convert unsigned byte to signed (-128 to +127)"""
    if value > 127:
        return value - 256
    return value
```

---

## Flag Behavior Cheat Sheet

| Instruction | Z | N | H | C |
|-------------|---|---|---|---|
| ADD         | ✓ | 0 | ✓ | ✓ |
| SUB         | ✓ | 1 | ✓ | ✓ |
| AND         | ✓ | 0 | 1 | 0 |
| OR          | ✓ | 0 | 0 | 0 |
| XOR         | ✓ | 0 | 0 | 0 |
| CP          | ✓ | 1 | ✓ | ✓ |
| INC (8bit)  | ✓ | 0 | ✓ | - |
| DEC (8bit)  | ✓ | 1 | ✓ | - |
| INC (16bit) | - | - | - | - |
| SCF         | - | 0 | 0 | 1 |
| CCF         | - | 0 | 0 | ✓ |
| CPL         | - | 1 | 1 | - |
| LD          | - | - | - | - |
| PUSH/POP    | - | - | - | - |
| JP/JR       | - | - | - | - |

Legend:
- ✓ = Affected (calculated based on result)
- 0 = Reset to 0
- 1 = Set to 1
- \- = Not affected

---

## Tips

1. **Always check flags** - Most bugs come from wrong flag behavior
2. **Use https://gbdev.io/gb-opcodes/** - Click opcode for exact behavior
3. **Relative jumps are signed** - JR takes -128 to +127 offset
4. **Stack grows downward** - PUSH decrements SP, POP increments SP
5. **HL is special** - Used as memory pointer in many instructions
6. **XOR A is common** - Fastest way to clear A to 0

---

## When You Hit a Missing Opcode

1. Look up in opcodes.py
2. Check if it's CB-prefixed (0xCB followed by another byte)
3. Add to cpu_decoder.py decode logic
4. Implement in instructions_impl.py
5. Add to execute_instruction() dispatcher
6. Test with Blargg ROM
7. Commit!

You're ready to tackle any opcode that comes your way!
