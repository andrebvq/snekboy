"""
Implementation of Game Boy CPU instructions

This module contains the actual execution logic for all instructions.
Separated from cpu.py for better organization.
"""

from src.utils import validate_byte, validate_word


class InstructionImplementations:
    """Mixin class containing all instruction implementations"""

    def _execute_scf(self) -> None:
        """SCF - Set Carry Flag"""
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = True
        # Zero flag not affected

    def _execute_ccf(self) -> None:
        """CCF - Complement Carry Flag"""
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = not self.registers.flags.carry
        # Zero flag not affected

    def _execute_cpl(self) -> None:
        """CPL - Complement A (flip all bits)"""
        self.registers._a = validate_byte(~self.registers._a)
        self.registers.flags.subtract = True
        self.registers.flags.half_carry = True
        # Zero and carry flags not affected

    def _execute_daa(self) -> None:
        """
        DAA - Decimal Adjust Accumulator

        Adjusts the result of BCD (Binary Coded Decimal) addition/subtraction.
        This is complex - used for decimal arithmetic in games.
        """
        a = self.registers._a
        correction = 0

        if self.registers.flags.subtract:
            # After subtraction
            if self.registers.flags.half_carry:
                correction |= 0x06
            if self.registers.flags.carry:
                correction |= 0x60
            a = (a - correction) & 0xFF
        else:
            # After addition
            if self.registers.flags.half_carry or (a & 0x0F) > 0x09:
                correction |= 0x06
            if self.registers.flags.carry or a > 0x99:
                correction |= 0x60
            a = (a + correction) & 0xFF

        self.registers._a = a
        self.registers.flags.zero = (a == 0)
        self.registers.flags.half_carry = False

        if correction & 0x60:
            self.registers.flags.carry = True

    def _execute_and(self, target, immediate_value=None) -> None:
        """AND - Logical AND with A"""
        value = self._get_operand_value(target, immediate_value)

        result = self.registers._a & value
        self.registers._a = validate_byte(result)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = True  # Always set for AND
        self.registers.flags.carry = False

    def _execute_or(self, target, immediate_value=None) -> None:
        """OR - Logical OR with A"""
        value = self._get_operand_value(target, immediate_value)

        result = self.registers._a | value
        self.registers._a = validate_byte(result)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = False

    def _execute_xor(self, target, immediate_value=None) -> None:
        """XOR - Logical XOR with A"""
        value = self._get_operand_value(target, immediate_value)

        result = self.registers._a ^ value
        self.registers._a = validate_byte(result)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = False

    def _execute_cp(self, target, immediate_value=None) -> None:
        """
        CP - Compare A with operand

        Performs A - operand and sets flags, but doesn't store result.
        Used for conditional jumps.
        """
        value = self._get_operand_value(target, immediate_value)

        result = self.registers._a - value

        # Set flags (same as SUB but don't store result)
        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = True
        self.registers.flags.half_carry = (self.registers._a & 0xF) < (value & 0xF)
        self.registers.flags.carry = result < 0

    def _execute_inc(self, target) -> None:
        """INC - Increment register or memory"""
        # Get current value
        if target == '(HL)':
            value = self.memory.read_byte(self.registers.hl)
        else:
            value = self._get_register_value(target)

        # Increment
        result = (value + 1) & 0xFF

        # Set flags (carry not affected!)
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = (value & 0xF) == 0xF

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_dec(self, target) -> None:
        """DEC - Decrement register or memory"""
        # Get current value
        if target == '(HL)':
            value = self.memory.read_byte(self.registers.hl)
        else:
            value = self._get_register_value(target)

        # Decrement
        result = (value - 1) & 0xFF

        # Set flags (carry not affected!)
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = True
        self.registers.flags.half_carry = (value & 0xF) == 0

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_push(self, register_pair) -> None:
        """PUSH - Push 16-bit register onto stack"""
        # Get value
        if register_pair == 'AF':
            value = self.registers.af
        elif register_pair == 'BC':
            value = self.registers.bc
        elif register_pair == 'DE':
            value = self.registers.de
        elif register_pair == 'HL':
            value = self.registers.hl
        else:
            raise ValueError(f"Unknown register pair for PUSH: {register_pair}")

        # Push onto stack (SP decrements)
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, (value >> 8) & 0xFF)  # High byte
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, value & 0xFF)  # Low byte

    def _execute_pop(self, register_pair) -> None:
        """POP - Pop 16-bit value from stack into register"""
        # Pop from stack (SP increments)
        low_byte = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)
        high_byte = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)

        value = (high_byte << 8) | low_byte

        # Set register pair
        if register_pair == 'AF':
            self.registers.af = value
        elif register_pair == 'BC':
            self.registers.bc = value
        elif register_pair == 'DE':
            self.registers.de = value
        elif register_pair == 'HL':
            self.registers.hl = value
        else:
            raise ValueError(f"Unknown register pair for POP: {register_pair}")

    def _execute_di(self) -> None:
        """DI - Disable Interrupts"""
        self.ime = False

    def _execute_ei(self) -> None:
        """EI - Enable Interrupts"""
        # EI enables interrupts AFTER the next instruction (Game Boy quirk)
        self._ei_pending = True

    # === CONTROL FLOW INSTRUCTIONS ===

    def _execute_jp(self, address, condition=None) -> None:
        """JP - Jump to address (unconditional or conditional)"""
        should_jump = self._check_condition(condition)

        if should_jump:
            self.registers._pc = validate_word(address)

    def _execute_jp_hl(self) -> None:
        """JP (HL) - Jump to address in HL"""
        self.registers._pc = self.registers.hl

    def _execute_jr(self, offset, condition=None) -> None:
        """JR - Relative jump (signed 8-bit offset)"""
        should_jump = self._check_condition(condition)

        if should_jump:
            # offset is signed 8-bit: -128 to +127
            if offset > 127:
                offset = offset - 256  # Convert to signed

            self.registers._pc = validate_word(self.registers._pc + offset)

    def _execute_call(self, address, condition=None) -> None:
        """CALL - Call subroutine (push PC, then jump)"""
        should_call = self._check_condition(condition)

        if should_call:
            # Push current PC onto stack
            self.registers._sp = validate_word(self.registers._sp - 1)
            self.memory.write_byte(self.registers._sp, (self.registers._pc >> 8) & 0xFF)
            self.registers._sp = validate_word(self.registers._sp - 1)
            self.memory.write_byte(self.registers._sp, self.registers._pc & 0xFF)

            # Jump to address
            self.registers._pc = validate_word(address)

    def _execute_ret(self, condition=None) -> None:
        """RET - Return from subroutine (pop PC from stack)"""
        should_ret = self._check_condition(condition)

        if should_ret:
            # Pop PC from stack
            low = self.memory.read_byte(self.registers._sp)
            self.registers._sp = validate_word(self.registers._sp + 1)
            high = self.memory.read_byte(self.registers._sp)
            self.registers._sp = validate_word(self.registers._sp + 1)

            self.registers._pc = (high << 8) | low

    # === ROTATE AND SHIFT INSTRUCTIONS ===

    def _execute_rlca(self) -> None:
        """RLCA - Rotate Left Circular Accumulator"""
        carry_bit = (self.registers._a >> 7) & 1
        self.registers._a = ((self.registers._a << 1) | carry_bit) & 0xFF

        self.registers.flags.zero = False  # RLCA always resets Z
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

    def _execute_rla(self) -> None:
        """RLA - Rotate Left through carry"""
        old_carry = 1 if self.registers.flags.carry else 0
        new_carry = (self.registers._a >> 7) & 1

        self.registers._a = ((self.registers._a << 1) | old_carry) & 0xFF

        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (new_carry == 1)

    def _execute_rrca(self) -> None:
        """RRCA - Rotate Right Circular"""
        carry_bit = self.registers._a & 1
        self.registers._a = (self.registers._a >> 1) | (carry_bit << 7)

        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

    def _execute_rra(self) -> None:
        """RRA - Rotate Right through carry"""
        old_carry = 1 if self.registers.flags.carry else 0
        new_carry = self.registers._a & 1

        self.registers._a = (self.registers._a >> 1) | (old_carry << 7)

        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (new_carry == 1)

    # === 16-BIT ARITHMETIC ===

    def _execute_inc_16(self, register_pair) -> None:
        """INC rr - Increment 16-bit register"""
        if register_pair == 'BC':
            self.registers.bc = validate_word(self.registers.bc + 1)
        elif register_pair == 'DE':
            self.registers.de = validate_word(self.registers.de + 1)
        elif register_pair == 'HL':
            self.registers.hl = validate_word(self.registers.hl + 1)
        elif register_pair == 'SP':
            self.registers._sp = validate_word(self.registers._sp + 1)
        else:
            raise ValueError(f"Unknown register pair for INC: {register_pair}")
        # No flags affected!

    def _execute_dec_16(self, register_pair) -> None:
        """DEC rr - Decrement 16-bit register"""
        if register_pair == 'BC':
            self.registers.bc = validate_word(self.registers.bc - 1)
        elif register_pair == 'DE':
            self.registers.de = validate_word(self.registers.de - 1)
        elif register_pair == 'HL':
            self.registers.hl = validate_word(self.registers.hl - 1)
        elif register_pair == 'SP':
            self.registers._sp = validate_word(self.registers._sp - 1)
        else:
            raise ValueError(f"Unknown register pair for DEC: {register_pair}")
        # No flags affected!

    def _execute_add_hl(self, source) -> None:
        """ADD HL,rr - Add 16-bit register to HL"""
        hl = self.registers.hl

        if source == 'BC':
            value = self.registers.bc
        elif source == 'DE':
            value = self.registers.de
        elif source == 'HL':
            value = self.registers.hl
        elif source == 'SP':
            value = self.registers._sp
        else:
            raise ValueError(f"Unknown source for ADD HL: {source}")

        result = hl + value

        self.registers.hl = validate_word(result)

        # Flags (Zero NOT affected)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = ((hl & 0x0FFF) + (value & 0x0FFF)) > 0x0FFF
        self.registers.flags.carry = result > 0xFFFF

    # === MORE LD VARIANTS ===

    def _execute_ldi(self, target, source) -> None:
        """LDI - Load and increment HL"""
        if target == '(HL)' and source == 'A':
            self.memory.write_byte(self.registers.hl, self.registers._a)
            self.registers.hl = validate_word(self.registers.hl + 1)
        elif target == 'A' and source == '(HL)':
            self.registers._a = self.memory.read_byte(self.registers.hl)
            self.registers.hl = validate_word(self.registers.hl + 1)
        else:
            raise ValueError(f"Unknown LDI operands: {target}, {source}")

    def _execute_ldd(self, target, source) -> None:
        """LDD - Load and decrement HL"""
        if target == '(HL)' and source == 'A':
            self.memory.write_byte(self.registers.hl, self.registers._a)
            self.registers.hl = validate_word(self.registers.hl - 1)
        elif target == 'A' and source == '(HL)':
            self.registers._a = self.memory.read_byte(self.registers.hl)
            self.registers.hl = validate_word(self.registers.hl - 1)
        else:
            raise ValueError(f"Unknown LDD operands: {target}, {source}")

    def _execute_ldh(self, target, source) -> None:
        """LDH - Load from/to high memory (0xFF00 + offset)"""
        if target == '(n)':
            # LDH (n),A - Store A at 0xFF00 + n
            offset = source if isinstance(source, int) else 0
            address = 0xFF00 + offset
            self.memory.write_byte(address, self.registers._a)
        elif source == '(n)':
            # LDH A,(n) - Load from 0xFF00 + n into A
            offset = target if isinstance(target, int) else 0
            address = 0xFF00 + offset
            self.registers._a = self.memory.read_byte(address)
        elif target == '(C)':
            # LDH (C),A - Store A at 0xFF00 + C
            address = 0xFF00 + self.registers._c
            self.memory.write_byte(address, self.registers._a)
        elif source == '(C)':
            # LDH A,(C) - Load from 0xFF00 + C into A
            address = 0xFF00 + self.registers._c
            self.registers._a = self.memory.read_byte(address)

    def _execute_ld_addr(self, target, source) -> None:
        """LD (nn),A / LD A,(nn) - Load to/from absolute address"""
        if target == 'A':
            # LD A,(nn) - Load from address into A
            address = source if isinstance(source, int) else 0
            self.registers._a = self.memory.read_byte(address)
        else:
            # LD (nn),A - Store A at address
            address = target if isinstance(target, int) else 0
            self.memory.write_byte(address, self.registers._a)

    def _execute_ld_nn_sp(self, address) -> None:
        """LD (nn),SP - Store SP at address (little-endian)"""
        self.memory.write_byte(address, self.registers._sp & 0xFF)
        self.memory.write_byte(address + 1, (self.registers._sp >> 8) & 0xFF)

    def _execute_add_sp_n(self, offset) -> None:
        """ADD SP,n - Add signed byte to SP"""
        # offset is signed 8-bit
        if offset > 127:
            offset = offset - 256

        # Save original SP for flag calculations
        sp_before = self.registers._sp
        result = sp_before + offset

        self.registers._sp = validate_word(result)

        # Flags
        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        # Half-carry and carry are set based on lower byte addition
        self.registers.flags.half_carry = ((sp_before & 0xF) + (offset & 0xF)) > 0xF
        self.registers.flags.carry = ((sp_before & 0xFF) + (offset & 0xFF)) > 0xFF

    def _execute_ld_hl_sp_n(self, offset) -> None:
        """LD HL,SP+n - Load SP + signed offset into HL"""
        # offset is signed 8-bit
        if offset > 127:
            offset = offset - 256

        result = self.registers._sp + offset

        self.registers.hl = validate_word(result)

        # Flags
        self.registers.flags.zero = False
        self.registers.flags.subtract = False
        # Half-carry and carry are set based on lower byte addition
        self.registers.flags.half_carry = ((self.registers._sp & 0xF) + (offset & 0xF)) > 0xF
        self.registers.flags.carry = ((self.registers._sp & 0xFF) + (offset & 0xFF)) > 0xFF

    def _execute_ld_sp_hl(self) -> None:
        """LD SP,HL - Load HL into SP"""
        self.registers._sp = self.registers.hl

    # === ADC AND SBC ===

    def _execute_adc(self, target, immediate_value=None) -> None:
        """ADC - Add with carry"""
        value = self._get_operand_value(target, immediate_value)
        carry = 1 if self.registers.flags.carry else 0

        current_a = self.registers._a
        result = current_a + value + carry

        # Set flags
        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = ((current_a & 0xF) + (value & 0xF) + carry) > 0xF
        self.registers.flags.carry = result > 0xFF

        # Store result
        self.registers._a = validate_byte(result)

    def _execute_sbc(self, target, immediate_value=None) -> None:
        """SBC - Subtract with carry"""
        value = self._get_operand_value(target, immediate_value)
        carry = 1 if self.registers.flags.carry else 0

        current_a = self.registers._a
        result = current_a - value - carry

        # Set flags
        self.registers.flags.zero = (result & 0xFF) == 0
        self.registers.flags.subtract = True
        self.registers.flags.half_carry = ((current_a & 0xF) - (value & 0xF) - carry) < 0
        self.registers.flags.carry = result < 0

        # Store result
        self.registers._a = validate_byte(result)

    # === RETI AND RST ===

    def _execute_reti(self) -> None:
        """RETI - Return from interrupt (same as RET but also enables interrupts)"""
        # Pop PC from stack
        low = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)
        high = self.memory.read_byte(self.registers._sp)
        self.registers._sp = validate_word(self.registers._sp + 1)

        self.registers._pc = (high << 8) | low

        # Enable interrupts (TODO: implement IME flag)
        pass

    def _execute_rst(self, vector) -> None:
        """RST - Restart (call to fixed address)"""
        # Push current PC onto stack
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, (self.registers._pc >> 8) & 0xFF)
        self.registers._sp = validate_word(self.registers._sp - 1)
        self.memory.write_byte(self.registers._sp, self.registers._pc & 0xFF)

        # Jump to vector
        self.registers._pc = validate_word(vector)

    # Helper methods
    def _check_condition(self, condition) -> bool:
        """Check if a condition is met for conditional jumps/calls/returns"""
        if condition is None:
            return True  # Unconditional

        if condition == 'NZ':
            return not self.registers.flags.zero
        elif condition == 'Z':
            return self.registers.flags.zero
        elif condition == 'NC':
            return not self.registers.flags.carry
        elif condition == 'C':
            return self.registers.flags.carry
        else:
            raise ValueError(f"Unknown condition: {condition}")

    # Helper methods
    def _get_operand_value(self, target, immediate_value=None):
        """Get value from operand (register, immediate, or memory)"""
        if isinstance(target, int):
            # Immediate value
            return target
        elif immediate_value is not None:
            return immediate_value
        elif target == '(HL)':
            return self.memory.read_byte(self.registers.hl)
        elif target == '(BC)':
            return self.memory.read_byte(self.registers.bc)
        elif target == '(DE)':
            return self.memory.read_byte(self.registers.de)
        else:
            return self._get_register_value(target)

    def _get_register_value(self, register):
        """Get value from 8-bit register"""
        register_map = {
            'A': self.registers._a,
            'B': self.registers._b,
            'C': self.registers._c,
            'D': self.registers._d,
            'E': self.registers._e,
            'H': self.registers._h,
            'L': self.registers._l,
        }
        return register_map.get(register, 0)

    def _set_register_value(self, register, value):
        """Set value to 8-bit register"""
        value = validate_byte(value)
        if register == 'A':
            self.registers._a = value
        elif register == 'B':
            self.registers._b = value
        elif register == 'C':
            self.registers._c = value
        elif register == 'D':
            self.registers._d = value
        elif register == 'E':
            self.registers._e = value
        elif register == 'H':
            self.registers._h = value
        elif register == 'L':
            self.registers._l = value
        else:
            raise ValueError(f"Unknown register: {register}")

    # === CB-PREFIXED INSTRUCTIONS ===

    def _execute_rlc(self, target) -> None:
        """RLC - Rotate Left Circular"""
        value = self._get_operand_value(target)
        carry_bit = (value >> 7) & 1
        result = ((value << 1) | carry_bit) & 0xFF

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_rrc(self, target) -> None:
        """RRC - Rotate Right Circular"""
        value = self._get_operand_value(target)
        carry_bit = value & 1
        result = (value >> 1) | (carry_bit << 7)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_rl(self, target) -> None:
        """RL - Rotate Left through carry"""
        value = self._get_operand_value(target)
        old_carry = 1 if self.registers.flags.carry else 0
        new_carry = (value >> 7) & 1
        result = ((value << 1) | old_carry) & 0xFF

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (new_carry == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_rr(self, target) -> None:
        """RR - Rotate Right through carry"""
        value = self._get_operand_value(target)
        old_carry = 1 if self.registers.flags.carry else 0
        new_carry = value & 1
        result = (value >> 1) | (old_carry << 7)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (new_carry == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_sla(self, target) -> None:
        """SLA - Shift Left Arithmetic (0 into LSB)"""
        value = self._get_operand_value(target)
        carry_bit = (value >> 7) & 1
        result = (value << 1) & 0xFF

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_sra(self, target) -> None:
        """SRA - Shift Right Arithmetic (MSB stays the same)"""
        value = self._get_operand_value(target)
        msb = value & 0x80  # Preserve MSB
        carry_bit = value & 1
        result = (value >> 1) | msb

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_srl(self, target) -> None:
        """SRL - Shift Right Logical (0 into MSB)"""
        value = self._get_operand_value(target)
        carry_bit = value & 1
        result = value >> 1

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = (carry_bit == 1)

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_swap(self, target) -> None:
        """SWAP - Swap upper and lower nibbles"""
        value = self._get_operand_value(target)
        result = ((value & 0x0F) << 4) | ((value & 0xF0) >> 4)

        # Set flags
        self.registers.flags.zero = (result == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = False
        self.registers.flags.carry = False

        # Store result
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_bit(self, target, bit_number) -> None:
        """BIT - Test bit (set Z flag if bit is 0)"""
        value = self._get_operand_value(target)
        bit_value = (value >> bit_number) & 1

        # Set flags
        self.registers.flags.zero = (bit_value == 0)
        self.registers.flags.subtract = False
        self.registers.flags.half_carry = True

    def _execute_res(self, target, bit_number) -> None:
        """RES - Reset bit (set bit to 0)"""
        value = self._get_operand_value(target)
        result = value & ~(1 << bit_number)

        # Store result (no flags affected)
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)

    def _execute_set(self, target, bit_number) -> None:
        """SET - Set bit (set bit to 1)"""
        value = self._get_operand_value(target)
        result = value | (1 << bit_number)

        # Store result (no flags affected)
        if target == '(HL)':
            self.memory.write_byte(self.registers.hl, result)
        else:
            self._set_register_value(target, result)
