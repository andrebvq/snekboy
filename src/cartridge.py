"""
Cartridge memory bank controllers (MBCs).

A cartridge exposes 32 KB of ROM (0x0000-0x7FFF) and up to 8 KB of RAM
(0xA000-0xBFFF) at a time. Larger games contain a mapper chip that switches
which 16 KB ROM bank and 8 KB RAM bank are visible. Games control it by
writing to the (read-only) ROM area: the write never changes ROM, it sets a
mapper register instead.

Memory keeps the visible ROM banks in its own array for fast reads and asks
the cartridge which banks to show after each ROM-area write. Cartridge RAM is
always accessed through the cartridge.

Reference: Pan Docs, "MBCs".
"""

import json
import time

ROM_BANK = 0x4000
RAM_BANK = 0x2000

# Header 0x0149 -> external RAM size in bytes
RAM_SIZES = {0x00: 0, 0x01: 0x800, 0x02: 0x2000, 0x03: 0x8000, 0x04: 0x20000, 0x05: 0x10000}


class Cartridge:
    """ROM only, optionally with up to 8 KB RAM (no banking)."""

    name = "ROM only"

    def __init__(self, rom: bytes, ram_size: int = 0, battery: bool = False):
        # Pad to a power-of-two number of 16 KB banks (at least 2) so bank
        # numbers can be masked like the real chips do.
        banks = 2
        while banks * ROM_BANK < len(rom):
            banks *= 2
        self.rom = bytearray(rom) + bytearray([0xFF] * (banks * ROM_BANK - len(rom)))
        self.rom_banks = banks
        self.ram = bytearray(ram_size)
        self.battery = battery
        self.ram_enabled = False
        # Banks currently visible at 0x0000-0x3FFF and 0x4000-0x7FFF
        self.bank0 = 0
        self.bankn = 1

    # --- ROM area writes (mapper registers) ---

    def write_rom(self, address: int, value: int) -> bool:
        """Handle a write to 0x0000-0x7FFF. Returns True if the ROM mapping changed."""
        return False

    # --- External RAM (0xA000-0xBFFF) ---

    def read_ram(self, address: int) -> int:
        if not self.ram:
            return 0xFF
        return self.ram[(address - 0xA000) % len(self.ram)]

    def write_ram(self, address: int, value: int) -> None:
        if self.ram:
            self.ram[(address - 0xA000) % len(self.ram)] = value

    # --- Battery saves ---

    def save(self, path: str) -> None:
        if self.battery and self.ram:
            with open(path, "wb") as f:
                f.write(self.ram)

    def load(self, path: str) -> None:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            return
        self.ram[:len(data)] = data[:len(self.ram)]


class MBC1(Cartridge):
    """Up to 2 MB ROM / 32 KB RAM."""

    name = "MBC1"

    def __init__(self, rom, ram_size=0, battery=False):
        super().__init__(rom, ram_size, battery)
        self.bank1 = 1      # 5 bits, 0x2000-0x3FFF
        self.bank2 = 0      # 2 bits, 0x4000-0x5FFF (upper ROM bits or RAM bank)
        self.mode = 0       # 0x6000-0x7FFF

    def write_rom(self, address, value):
        if address < 0x2000:
            self.ram_enabled = (value & 0x0F) == 0x0A
            return False
        if address < 0x4000:
            self.bank1 = (value & 0x1F) or 1     # bank 0 can't be selected here
        elif address < 0x6000:
            self.bank2 = value & 0x03
        else:
            self.mode = value & 0x01
        return self._update_banks()

    def _update_banks(self):
        mask = self.rom_banks - 1
        old = (self.bank0, self.bankn)
        self.bank0 = ((self.bank2 << 5) if self.mode else 0) & mask
        self.bankn = ((self.bank2 << 5) | self.bank1) & mask
        return (self.bank0, self.bankn) != old

    def _ram_offset(self, address):
        bank = self.bank2 if (self.mode and len(self.ram) > RAM_BANK) else 0
        return (bank * RAM_BANK + address - 0xA000) % len(self.ram)

    def read_ram(self, address):
        if not (self.ram_enabled and self.ram):
            return 0xFF
        return self.ram[self._ram_offset(address)]

    def write_ram(self, address, value):
        if self.ram_enabled and self.ram:
            self.ram[self._ram_offset(address)] = value


class MBC2(Cartridge):
    """Up to 256 KB ROM, built-in 512 x 4-bit RAM."""

    name = "MBC2"

    def __init__(self, rom, ram_size=0, battery=False):
        super().__init__(rom, 512, battery)

    def write_rom(self, address, value):
        if address >= 0x4000:
            return False
        if address & 0x0100:                  # address bit 8 set: ROM bank
            old = self.bankn
            self.bankn = ((value & 0x0F) or 1) & (self.rom_banks - 1)
            return self.bankn != old
        self.ram_enabled = (value & 0x0F) == 0x0A
        return False

    def read_ram(self, address):
        if not self.ram_enabled:
            return 0xFF
        return 0xF0 | self.ram[address & 0x01FF]   # upper 4 bits don't exist

    def write_ram(self, address, value):
        if self.ram_enabled:
            self.ram[address & 0x01FF] = value & 0x0F


class MBC3(Cartridge):
    """Up to 2 MB ROM / 32 KB RAM, optional real-time clock (RTC)."""

    name = "MBC3"

    def __init__(self, rom, ram_size=0, battery=False, rtc=False, clock=time.time):
        super().__init__(rom, ram_size, battery)
        self.has_rtc = rtc
        self.ram_bank = 0          # 0x00-0x03 RAM bank, 0x08-0x0C RTC register
        self._clock = clock
        # RTC: running total of seconds since "zero", measured from _ref_time
        self._rtc_seconds = 0
        self._ref_time = clock()
        self._rtc_halt = False
        self._rtc_carry = False
        self._latch_last = None
        self._latched = [0, 0, 0, 0, 0]

    def write_rom(self, address, value):
        if address < 0x2000:
            self.ram_enabled = (value & 0x0F) == 0x0A
        elif address < 0x4000:
            old = self.bankn
            self.bankn = ((value & 0x7F) or 1) & (self.rom_banks - 1)
            return self.bankn != old
        elif address < 0x6000:
            self.ram_bank = value & 0x0F
        elif self.has_rtc:
            if self._latch_last == 0x00 and value == 0x01:
                self._latched = self._rtc_registers()
            self._latch_last = value
        return False

    # --- RTC ---

    def _now_seconds(self):
        if self._rtc_halt:
            return self._rtc_seconds
        return self._rtc_seconds + int(self._clock() - self._ref_time)

    def _set_seconds(self, total):
        days = total // 86400
        if days > 0x1FF:                     # 9-bit day counter overflow
            self._rtc_carry = True
            total -= (days & ~0x1FF) * 86400
        self._rtc_seconds = total
        self._ref_time = self._clock()

    def _rtc_registers(self):
        total = self._now_seconds()
        days = total // 86400
        if days > 0x1FF:
            self._set_seconds(total)
            total, days = self._rtc_seconds, self._rtc_seconds // 86400
        day_high = ((days >> 8) & 0x01) | (0x40 if self._rtc_halt else 0) | (0x80 if self._rtc_carry else 0)
        return [total % 60, (total // 60) % 60, (total // 3600) % 24, days & 0xFF, day_high]

    def _write_rtc(self, reg, value):
        s, m, h, dl, dh = self._rtc_registers()
        days = dl | ((dh & 0x01) << 8)
        if reg == 0x08:
            s = value & 0x3F
        elif reg == 0x09:
            m = value & 0x3F
        elif reg == 0x0A:
            h = value & 0x1F
        elif reg == 0x0B:
            days = (days & 0x100) | value
        else:
            days = (days & 0xFF) | ((value & 0x01) << 8)
            self._rtc_carry = bool(value & 0x80)
        total = days * 86400 + h * 3600 + m * 60 + s
        halt = bool(value & 0x40) if reg == 0x0C else self._rtc_halt
        self._rtc_halt = False                 # store the new value un-halted
        self._set_seconds(total)
        self._rtc_halt = halt

    # --- RAM / RTC access ---

    def read_ram(self, address):
        if not self.ram_enabled:
            return 0xFF
        if 0x08 <= self.ram_bank <= 0x0C:
            return self._latched[self.ram_bank - 0x08] if self.has_rtc else 0xFF
        if not self.ram:
            return 0xFF
        return self.ram[(self.ram_bank * RAM_BANK + address - 0xA000) % len(self.ram)]

    def write_ram(self, address, value):
        if not self.ram_enabled:
            return
        if 0x08 <= self.ram_bank <= 0x0C:
            if self.has_rtc:
                self._write_rtc(self.ram_bank, value)
        elif self.ram:
            self.ram[(self.ram_bank * RAM_BANK + address - 0xA000) % len(self.ram)] = value

    # --- Saves: RAM in .sav, clock state in .rtc ---

    def save(self, path):
        super().save(path)
        if self.has_rtc and self.battery:
            with open(path[:-4] + ".rtc", "w") as f:
                json.dump({"seconds": self._now_seconds(), "time": self._clock(),
                           "halt": self._rtc_halt, "carry": self._rtc_carry}, f)

    def load(self, path):
        super().load(path)
        if not self.has_rtc:
            return
        try:
            with open(path[:-4] + ".rtc") as f:
                state = json.load(f)
        except (FileNotFoundError, ValueError):
            return
        self._rtc_halt = state["halt"]
        self._rtc_carry = state["carry"]
        self._rtc_seconds = state["seconds"]
        # The clock keeps running while the emulator is closed (unless halted)
        self._ref_time = state["time"]


class MBC5(Cartridge):
    """Up to 8 MB ROM / 128 KB RAM."""

    name = "MBC5"

    def __init__(self, rom, ram_size=0, battery=False, rumble=False):
        super().__init__(rom, ram_size, battery)
        self.rom_bank = 1
        self.ram_bank = 0
        self.rumble = rumble

    def write_rom(self, address, value):
        if address < 0x2000:
            self.ram_enabled = value == 0x0A
            return False
        if address < 0x3000:
            self.rom_bank = (self.rom_bank & 0x100) | value
        elif address < 0x4000:
            self.rom_bank = (self.rom_bank & 0xFF) | ((value & 0x01) << 8)
        elif address < 0x6000:
            # On rumble carts bit 3 drives the motor instead of selecting RAM
            self.ram_bank = value & (0x07 if self.rumble else 0x0F)
            return False
        else:
            return False
        old = self.bankn
        self.bankn = self.rom_bank & (self.rom_banks - 1)   # bank 0 is allowed here
        return self.bankn != old

    def read_ram(self, address):
        if not (self.ram_enabled and self.ram):
            return 0xFF
        return self.ram[(self.ram_bank * RAM_BANK + address - 0xA000) % len(self.ram)]

    def write_ram(self, address, value):
        if self.ram_enabled and self.ram:
            self.ram[(self.ram_bank * RAM_BANK + address - 0xA000) % len(self.ram)] = value


def make_cartridge(rom: bytes) -> Cartridge:
    """Create the right cartridge for a ROM from its header (0x0147 type, 0x0149 RAM size)."""
    kind = rom[0x147] if len(rom) > 0x149 else 0x00
    ram = RAM_SIZES.get(rom[0x149], 0) if len(rom) > 0x149 else 0

    if kind == 0x00:
        return Cartridge(rom)
    if kind in (0x08, 0x09):
        return Cartridge(rom, ram, battery=kind == 0x09)
    if kind in (0x01, 0x02, 0x03):
        return MBC1(rom, ram if kind != 0x01 else 0, battery=kind == 0x03)
    if kind in (0x05, 0x06):
        return MBC2(rom, battery=kind == 0x06)
    if kind in (0x0F, 0x10, 0x11, 0x12, 0x13):
        return MBC3(rom, ram if kind in (0x10, 0x12, 0x13) else 0,
                    battery=kind in (0x0F, 0x10, 0x13), rtc=kind in (0x0F, 0x10))
    if 0x19 <= kind <= 0x1E:
        return MBC5(rom, ram if kind in (0x1A, 0x1B, 0x1D, 0x1E) else 0,
                    battery=kind in (0x1B, 0x1E), rumble=kind >= 0x1C)

    print(f"Warning: cartridge type 0x{kind:02X} is not supported; running as ROM only")
    return Cartridge(rom)
