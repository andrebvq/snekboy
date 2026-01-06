"""
Game Boy Timer Implementation

The timer system consists of 4 registers:
- DIV  (0xFF04): Divider register, increments at 16384 Hz (every 256 cycles)
- TIMA (0xFF05): Timer counter, increments at rate set by TAC
- TMA  (0xFF06): Timer modulo, value to reload TIMA on overflow
- TAC  (0xFF07): Timer control

TAC bits:
- Bit 2: Timer enable (1=on, 0=off)
- Bits 0-1: Clock select
  - 00: 4096 Hz   (increment TIMA every 1024 cycles)
  - 01: 262144 Hz (increment TIMA every 16 cycles)
  - 10: 65536 Hz  (increment TIMA every 64 cycles)
  - 11: 16384 Hz  (increment TIMA every 256 cycles)

When TIMA overflows (0xFF -> 0x00), it:
1. Triggers timer interrupt (IF bit 2)
2. Reloads from TMA
"""

class Timer:
    """Game Boy Timer"""

    # Clock frequencies (in cycles per increment)
    CLOCK_FREQUENCIES = {
        0: 1024,  # 4096 Hz
        1: 16,    # 262144 Hz
        2: 64,    # 65536 Hz
        3: 256,   # 16384 Hz
    }

    DIV_FREQUENCY = 256  # DIV increments every 256 cycles

    def __init__(self, interrupt_callback=None):
        """
        Initialize timer

        Args:
            interrupt_callback: Function to call when timer interrupt occurs
                              Should accept interrupt bit number (2 for timer)
        """
        self._div = 0          # Divider register (0xFF04)
        self._tima = 0         # Timer counter (0xFF05)
        self._tma = 0          # Timer modulo (0xFF06)
        self._tac = 0          # Timer control (0xFF07)

        self._div_counter = 0  # Internal counter for DIV
        self._tima_counter = 0 # Internal counter for TIMA

        self._interrupt_callback = interrupt_callback

    def read_byte(self, address: int) -> int:
        """Read timer register"""
        if address == 0xFF04:
            return self._div
        elif address == 0xFF05:
            return self._tima
        elif address == 0xFF06:
            return self._tma
        elif address == 0xFF07:
            return self._tac | 0xF8  # Upper bits always read as 1
        else:
            raise ValueError(f"Invalid timer address: 0x{address:04X}")

    def write_byte(self, address: int, value: int) -> None:
        """Write timer register"""
        value = value & 0xFF

        if address == 0xFF04:
            # Writing any value to DIV resets it to 0
            self._div = 0
            self._div_counter = 0
        elif address == 0xFF05:
            self._tima = value
        elif address == 0xFF06:
            self._tma = value
        elif address == 0xFF07:
            self._tac = value & 0x07  # Only lower 3 bits are writable
        else:
            raise ValueError(f"Invalid timer address: 0x{address:04X}")

    def tick(self, cycles: int) -> None:
        """
        Update timer for the given number of cycles

        Args:
            cycles: Number of CPU cycles that have elapsed
        """
        # Update DIV register
        self._div_counter += cycles
        while self._div_counter >= self.DIV_FREQUENCY:
            self._div = (self._div + 1) & 0xFF
            self._div_counter -= self.DIV_FREQUENCY

        # Update TIMA if enabled
        if self._is_timer_enabled():
            frequency = self._get_timer_frequency()
            self._tima_counter += cycles

            while self._tima_counter >= frequency:
                self._increment_tima()
                self._tima_counter -= frequency

    def _is_timer_enabled(self) -> bool:
        """Check if timer is enabled (TAC bit 2)"""
        return (self._tac & 0x04) != 0

    def _get_timer_frequency(self) -> int:
        """Get current timer frequency in cycles"""
        clock_select = self._tac & 0x03
        return self.CLOCK_FREQUENCIES[clock_select]

    def _increment_tima(self) -> None:
        """Increment TIMA and handle overflow"""
        self._tima = (self._tima + 1) & 0xFF

        # Check for overflow (wrapped from 0xFF to 0x00)
        if self._tima == 0:
            # Reload from TMA
            self._tima = self._tma

            # Request timer interrupt (bit 2)
            if self._interrupt_callback:
                self._interrupt_callback(2)

    def reset(self) -> None:
        """Reset timer to power-on state"""
        self._div = 0
        self._tima = 0
        self._tma = 0
        self._tac = 0
        self._div_counter = 0
        self._tima_counter = 0
