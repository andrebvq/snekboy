"""
Implementation of Game Boy CPU instructions

This module contains the actual execution logic for all instructions.
Separated from cpu.py for better organization.
"""

from utils import validate_byte, validate_word


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
        # TODO: Implement interrupt system
        pass  # For now, do nothing

    def _execute_ei(self) -> None:
        """EI - Enable Interrupts"""
        # TODO: Implement interrupt system
        pass  # For now, do nothing

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
