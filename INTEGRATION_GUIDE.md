# Integration Guide for New Instructions

## Files Created:
1. `src/instructions_impl.py` - Implementation of all instruction logic
2. `src/cpu_decoder.py` - Decoder for converting opcodes to instruction params
3. Updated `src/opcodes.py` - Added missing opcodes

## How to Integrate into Your CPU:

### Step 1: Update your cpu.py

At the top, add imports:

```python
from instructions_impl import InstructionImplementations
from cpu_decoder import InstructionType, decode_instruction_params
```

### Step 2: Make CPU inherit from InstructionImplementations

```python
class CPU(InstructionImplementations):  # Add this inheritance
    def __init__(self, memory=None):
        self.registers = Register()
        self.memory = memory if memory else Memory()
        self.total_cycles = 0
        self.halted = False
        self._initialize_state()
```

### Step 3: Update your decode() method

Replace your decode() method with:

```python
def decode(self, opcode: int):
    """Decode opcode into instruction parameters"""
    if opcode not in OPCODES:
        raise ValueError(f"Unknown opcode: 0x{opcode:02X} at PC=0x{self.registers._pc - 1:04X}")

    # Get opcode info
    info = OPCODES[opcode]
    name, length, cycles, flags = info

    # Decode parameters
    instr_type, target, immediate = decode_instruction_params(
        opcode,
        self.fetch_byte,
        self.fetch_word
    )

    if instr_type is None:
        raise NotImplementedError(
            f"Opcode 0x{opcode:02X} ({name}) not yet implemented at PC=0x{self.registers._pc - 1:04X}"
        )

    return (instr_type, target, immediate, cycles)
```

### Step 4: Update your step() method

```python
def step(self) -> int:
    """Execute one instruction"""
    if self.halted:
        return 4

    # FETCH
    opcode = self.fetch_byte()

    # DECODE
    instr_type, target, immediate, cycles = self.decode(opcode)

    # EXECUTE
    self.execute_instruction(instr_type, target, immediate)

    # UPDATE
    self.total_cycles += cycles

    return cycles
```

### Step 5: Add execute_instruction() dispatcher

```python
def execute_instruction(self, instr_type, target, immediate):
    """Dispatch instruction to appropriate handler"""

    if instr_type == InstructionType.NOP:
        pass

    elif instr_type == InstructionType.HALT:
        self.halted = True

    elif instr_type == InstructionType.STOP:
        self.halted = True  # Similar to HALT for now

    elif instr_type == InstructionType.ADD:
        self._execute_add(target, immediate)

    elif instr_type == InstructionType.SUB:
        self._execute_sub(target, immediate)

    elif instr_type == InstructionType.AND:
        self._execute_and(target, immediate)

    elif instr_type == InstructionType.OR:
        self._execute_or(target, immediate)

    elif instr_type == InstructionType.XOR:
        self._execute_xor(target, immediate)

    elif instr_type == InstructionType.CP:
        self._execute_cp(target, immediate)

    elif instr_type == InstructionType.INC:
        self._execute_inc(target)

    elif instr_type == InstructionType.DEC:
        self._execute_dec(target)

    elif instr_type == InstructionType.LD:
        self._execute_ld(target, immediate)

    elif instr_type == InstructionType.PUSH:
        self._execute_push(target)

    elif instr_type == InstructionType.POP:
        self._execute_pop(target)

    elif instr_type == InstructionType.SCF:
        self._execute_scf()

    elif instr_type == InstructionType.CCF:
        self._execute_ccf()

    elif instr_type == InstructionType.CPL:
        self._execute_cpl()

    elif instr_type == InstructionType.DAA:
        self._execute_daa()

    elif instr_type == InstructionType.DI:
        self._execute_di()

    elif instr_type == InstructionType.EI:
        self._execute_ei()

    else:
        raise NotImplementedError(f"Instruction {instr_type} not implemented")
```

### Step 6: Add SUB implementation

You have ADD already, now add SUB (very similar):

```python
def _execute_sub(self, target, immediate_value=None) -> None:
    """Execute SUB instruction"""
    value = self._get_operand_value(target, immediate_value)

    current_a = self.registers._a
    result = current_a - value

    # Set flags
    self.registers.flags.zero = (result & 0xFF) == 0
    self.registers.flags.subtract = True  # Different from ADD
    self.registers.flags.half_carry = (current_a & 0xF) < (value & 0xF)
    self.registers.flags.carry = result < 0

    # Store result
    self.registers._a = validate_byte(result)
```

## Testing Your Changes:

After integration, test with:

```bash
python tests/test_with_blargg.py
```

It should get further than before! You'll likely hit more missing opcodes (JP, JR, CALL, RET), but you now have the framework to add them easily.

## Quick Reference: What Each Instruction Does

- **SCF**: Set carry flag to 1
- **CCF**: Flip carry flag
- **CPL**: Flip all bits in A (bitwise NOT)
- **DAA**: Decimal adjust (for BCD arithmetic)
- **AND**: A = A & operand (sets half_carry=1, carry=0)
- **OR**: A = A | operand (clears half_carry and carry)
- **XOR**: A = A ^ operand (common: XOR A clears A to 0)
- **CP**: Compare (SUB but don't store result, just set flags)
- **INC**: Increment by 1 (doesn't affect carry flag!)
- **DEC**: Decrement by 1 (doesn't affect carry flag!)
- **PUSH**: Push 16-bit register onto stack, SP -= 2
- **POP**: Pop from stack into 16-bit register, SP += 2

## Common Pattern You'll See:

Many ROMs start with:
```
0x0100: NOP           ; Entry point
0x0101: LD SP,$FFFE  ; Initialize stack pointer
0x0104: XOR A        ; Clear A to 0
0x0105: LD HL,$9FFF  ; Set HL
...
```

Now you can handle most of these!
