"""
Game Boy Joypad (P1) implementation

P1 Register (0xFF00):
  Bit 7-6: Not used
  Bit 5: P15 Select Button Keys (0=Select)
  Bit 4: P14 Select Direction Keys (0=Select)
  Bit 3: P13 Input Down or Start (0=Pressed)
  Bit 2: P12 Input Up or Select (0=Pressed)
  Bit 1: P11 Input Left or B (0=Pressed)
  Bit 0: P10 Input Right or A (0=Pressed)

Reading works by:
1. Write to P1 to select button group (set bit 4 or 5 to 0)
2. Read P1 to get button states (bits 0-3)

Note: 0 = pressed, 1 = not pressed (inverted logic)
"""

class Joypad:
    """Game Boy joypad controller"""

    def __init__(self, interrupt_callback=None):
        """
        Initialize joypad state

        Args:
            interrupt_callback: Optional callback function to trigger joypad interrupt
                                Should take interrupt bit number as argument
        """
        self.interrupt_callback = interrupt_callback

        # Button states (True = pressed, False = not pressed)
        self.button_a = False
        self.button_b = False
        self.button_start = False
        self.button_select = False
        self.dpad_up = False
        self.dpad_down = False
        self.dpad_left = False
        self.dpad_right = False

        # P1 register state
        # True = this group IS selected (bit would be 0)
        # False = this group is NOT selected (bit would be 1)
        self.select_buttons = False   # Initially not selected
        self.select_dpad = False      # Initially not selected

    def write_p1(self, value: int) -> None:
        """
        Write to P1 register (0xFF00)

        Games write to select which button group to read
        Bit 5 = 0: Select button keys (A, B, Start, Select)
        Bit 4 = 0: Select direction keys (Up, Down, Left, Right)
        """
        # Only bits 4-5 are writable
        # Note: bit = 0 means selected, so we invert the logic
        self.select_buttons = (value & 0x20) == 0  # Bit 5 = 0 means buttons selected
        self.select_dpad = (value & 0x10) == 0     # Bit 4 = 0 means dpad selected

    def read_p1(self) -> int:
        """
        Read P1 register (0xFF00)

        Returns current button states based on selected group
        Bits 0-3 contain button state (0 = pressed, 1 = not pressed)
        """
        # Start with bits 6-7 always 1, bits 0-3 default to 1 (not pressed)
        result = 0xCF  # 11001111 (all buttons not pressed by default)

        # Set selection bits to reflect what's NOT selected
        # (remember: 0 = selected, 1 = not selected)
        if not self.select_buttons:
            result |= 0x20  # Bit 5 = 1 (buttons not selected)
        if not self.select_dpad:
            result |= 0x10  # Bit 4 = 1 (dpad not selected)

        # Return button states based on what's selected
        # Note: 0 = pressed, 1 = not pressed (inverted)
        # Use &= to CLEAR bits for pressed buttons (set to 0)

        # Check which group(s) are selected
        if self.select_buttons and self.select_dpad:
            # Both selected: OR of both groups
            if self.button_start or self.dpad_down:
                result &= ~0x08  # Clear bit 3
            if self.button_select or self.dpad_up:
                result &= ~0x04  # Clear bit 2
            if self.button_b or self.dpad_left:
                result &= ~0x02  # Clear bit 1
            if self.button_a or self.dpad_right:
                result &= ~0x01  # Clear bit 0

        elif self.select_buttons:
            # Only button keys selected
            if self.button_start:
                result &= ~0x08  # Clear bit 3: Start
            if self.button_select:
                result &= ~0x04  # Clear bit 2: Select
            if self.button_b:
                result &= ~0x02  # Clear bit 1: B
            if self.button_a:
                result &= ~0x01  # Clear bit 0: A

        elif self.select_dpad:
            # Only direction keys selected
            if self.dpad_down:
                result &= ~0x08  # Clear bit 3: Down
            if self.dpad_up:
                result &= ~0x04  # Clear bit 2: Up
            if self.dpad_left:
                result &= ~0x02  # Clear bit 1: Left
            if self.dpad_right:
                result &= ~0x01  # Clear bit 0: Right

        # If neither selected, all bits stay 1 (not pressed) - already set above

        return result

    def press_button(self, button: str) -> None:
        """Press a button (set it to pressed state and trigger interrupt)"""
        button = button.lower()
        if button == 'a':
            self.button_a = True
        elif button == 'b':
            self.button_b = True
        elif button == 'start':
            self.button_start = True
        elif button == 'select':
            self.button_select = True
        elif button == 'up':
            self.dpad_up = True
        elif button == 'down':
            self.dpad_down = True
        elif button == 'left':
            self.dpad_left = True
        elif button == 'right':
            self.dpad_right = True

        # Trigger joypad interrupt (bit 4 of IF register)
        if self.interrupt_callback:
            self.interrupt_callback(4)

    def release_button(self, button: str) -> None:
        """Release a button (set it to not pressed state)"""
        button = button.lower()
        if button == 'a':
            self.button_a = False
        elif button == 'b':
            self.button_b = False
        elif button == 'start':
            self.button_start = False
        elif button == 'select':
            self.button_select = False
        elif button == 'up':
            self.dpad_up = False
        elif button == 'down':
            self.dpad_down = False
        elif button == 'left':
            self.dpad_left = False
        elif button == 'right':
            self.dpad_right = False

    def release_all(self) -> None:
        """Release all buttons"""
        self.button_a = False
        self.button_b = False
        self.button_start = False
        self.button_select = False
        self.dpad_up = False
        self.dpad_down = False
        self.dpad_left = False
        self.dpad_right = False

    def get_state_string(self) -> str:
        """Get a string representation of current button states (for debugging)"""
        buttons = []
        if self.dpad_up: buttons.append('UP')
        if self.dpad_down: buttons.append('DOWN')
        if self.dpad_left: buttons.append('LEFT')
        if self.dpad_right: buttons.append('RIGHT')
        if self.button_a: buttons.append('A')
        if self.button_b: buttons.append('B')
        if self.button_start: buttons.append('START')
        if self.button_select: buttons.append('SELECT')
        return ' '.join(buttons) if buttons else 'none'
