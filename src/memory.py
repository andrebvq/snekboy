"""
Game Boy Memory Management Unit (MMU)

Memory Map:
0x0000-0x3FFF : ROM Bank 0 (16KB)
0x4000-0x7FFF : ROM Bank N (16KB, switchable)
0x8000-0x9FFF : VRAM (8KB)
0xA000-0xBFFF : External RAM (8KB, cartridge)
0xC000-0xDFFF : Work RAM (8KB)
0xE000-0xFDFF : Echo RAM (mirror of C000-DDFF)
0xFE00-0xFE9F : OAM (Sprite Attribute Table)
0xFEA0-0xFEFF : Unusable
0xFF00-0xFF7F : I/O Registers
0xFF80-0xFFFE : High RAM (HRAM)
0xFFFF        : Interrupt Enable Register
"""

from typing import Optional
from src.utils import validate_byte, validate_word, MemoryRanges
from src.joypad import Joypad
from src.cartridge import make_cartridge
from src.gameboy_doctor import should_override_ly_register, get_overridden_ly_value  # Gameboy Doctor integration

# Bits that always read as 1 for each I/O register 0xFF00-0xFF7F on DMG
# (unused bits, write-only bits, and unmapped registers = 0xFF). Pan Docs, "Hardware Registers".
_IO_READ_MASK = bytes([
    # FF00 P1, SB, SC, --, DIV, TIMA, TMA, TAC, --..--, IF
    0xC0, 0x00, 0x7E, 0xFF, 0x00, 0x00, 0x00, 0xF8, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xE0,
    # FF10 sound channel 1, 2
    0x80, 0x3F, 0x00, 0xFF, 0xBF, 0xFF, 0x3F, 0x00, 0xFF, 0xBF, 0x7F, 0xFF, 0x9F, 0xFF, 0xBF, 0xFF,
    # FF20 sound channel 4, control; FF27-FF2F unused
    0xFF, 0x00, 0x00, 0xBF, 0x00, 0x00, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    # FF30 wave RAM
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    # FF40 LCDC, STAT, SCY, SCX, LY, LYC, DMA, BGP, OBP0, OBP1, WY, WX; FF4C-FF4F unmapped
    0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
]) + bytes([0xFF] * 0x30)  # FF50-FF7F unmapped on DMG

class Memory:
    """Game Boy Memory Management Unit"""

    def __init__(self, cpu=None):
        # 64KB address space (0x0000 to 0xFFFF)
        self._data = bytearray(65536)

        # Serial buffer for test ROM output
        self._serial_buffer = 0
        self._serial_output = []  # Capture all serial output

        # Reference to CPU for timer reset and interrupts
        self._cpu = cpu

        # Flag to bypass PPU mode restrictions (for internal PPU access)
        self._bypass_ppu_restrictions = False

        # Joypad controller (needs CPU for interrupt callback)
        if cpu:
            self.joypad = Joypad(interrupt_callback=cpu._request_interrupt)
        else:
            self.joypad = Joypad()

        # Interrupt registers
        # IE (0xFFFF) - Interrupt Enable
        # IF (0xFF0F) - Interrupt Flags
        # Both are readable/writable, initialized to 0
        self._data[0xFFFF] = 0x00  # IE register
        self._data[0xFF0F] = 0x00  # IF register

        # Optional: Track read/write for debugging
        self._read_count = 0
        self._write_count = 0

        # OAM DMA state
        self._dma_active = False
        self._dma_cycles_remaining = 0
        self._dma_source = 0

        # Boot ROM state
        self.boot_rom_enabled = True  # Boot ROM active until 0xFF50 write
        self.cartridge_data = None  # Will store full cartridge ROM
        self.cartridge = None  # Memory bank controller, set by load_rom
        # Gameboy Doctor LY override, read once: checking the environment on
        # every LY read was a measurable cost (games poll LY constantly).
        self._doctor_ly_override = should_override_ly_register()
    
    def read_byte(self, address: int) -> int:
        """Read a single byte from memory"""
        address &= 0xFFFF
        self._read_count += 1

        # Fast path for the most common reads: ROM (instruction fetches),
        # work RAM, high RAM and IE have no special read rules.
        if address < 0x8000:
            # Boot ROM mapping (0x0000-0x00FF) - active until FF50 write.
            # Boot ROM not loaded - return cartridge data.
            if address < 0x0100 and self.boot_rom_enabled and self.cartridge_data:
                return self.cartridge_data[address]
            return self._data[address]
        if 0xC000 <= address < 0xE000 or address >= 0xFF80:
            return self._data[address]

        # Cartridge RAM (0xA000-0xBFFF) goes through the memory bank controller
        if 0xA000 <= address <= 0xBFFF and self.cartridge:
            return self.cartridge.read_ram(address)

        # Check for OAM access restrictions during PPU modes (only for CPU reads, not PPU reads)
        # OAM (0xFE00-0xFE9F) is blocked during Mode 2 (OAM Search) and Mode 3 (Pixel Transfer)
        # BUT only when LCD is enabled (LCDC bit 7)
        # The unusable area 0xFEA0-0xFEFF follows the same lock.
        if not self._bypass_ppu_restrictions and 0xFE00 <= address <= 0xFEFF:
            if self._cpu and hasattr(self._cpu, 'ppu'):
                lcdc = self._data[0xFF40]
                if lcdc & 0x80:  # LCD is ON
                    ppu_mode = self._cpu.ppu.current_mode
                    # Mode 2 = OAM Search, Mode 3 = Pixel Transfer
                    if ppu_mode == 2 or ppu_mode == 3:
                        return 0xFF  # Return 0xFF for blocked reads

        # Unusable area reads 0x00 on DMG when not locked.
        if 0xFEA0 <= address <= 0xFEFF:
            return 0x00

        # Check for VRAM access restrictions during PPU Mode 3 (only for CPU reads, not PPU reads)
        # VRAM (0x8000-0x9FFF) is blocked during Mode 3 (Pixel Transfer)
        # BUT only when LCD is enabled (LCDC bit 7)
        if not self._bypass_ppu_restrictions and 0x8000 <= address <= 0x9FFF:
            if self._cpu and hasattr(self._cpu, 'ppu'):
                lcdc = self._data[0xFF40]
                if lcdc & 0x80:  # LCD is ON
                    ppu_mode = self._cpu.ppu.current_mode
                    if ppu_mode == 3:  # Mode 3 = Pixel Transfer
                        return 0xFF  # Return 0xFF for blocked reads

        # P1/JOYP register (0xFF00) - Joypad
        if address == 0xFF00:
            return self.joypad.read_p1()

        # Gameboy Doctor: Override LY register to 0x90 (VBlank) to avoid timing issues
        if address == 0xFF44 and self._doctor_ly_override:
            return get_overridden_ly_value()

        # Handle special memory regions
        if address >= MemoryRanges.ECHO_RAM_START and address <= MemoryRanges.ECHO_RAM_END:
            # Echo RAM mirrors C000-DDFF
            mirror_address = address - 0x2000
            return int(self._data[mirror_address])

        if 0xFF00 <= address <= 0xFF7F:
            return self._data[address] | _IO_READ_MASK[address - 0xFF00]

        return int(self._data[address])
    
    def write_byte(self, address: int, value: int) -> None:
        """Write byte with serial port handling"""
        address = validate_word(address)
        value = validate_byte(value)

        # ROM (0x0000-0x7FFF) is read-only. Writes here set cartridge
        # mapper (MBC) registers, e.g. to switch ROM banks.
        if address < 0x8000:
            if self.cartridge and self.cartridge.write_rom(address, value):
                self._map_rom()
            return

        if 0xA000 <= address <= 0xBFFF and self.cartridge:
            self.cartridge.write_ram(address, value)
            return

        # Echo RAM (0xE000-0xFDFF) is the same memory as 0xC000-0xDDFF.
        if 0xE000 <= address <= 0xFDFF:
            address -= 0x2000

        # 0xFEA0-0xFEFF is unusable; writes have no effect.
        if 0xFEA0 <= address <= 0xFEFF:
            return

        # Check for OAM write restrictions during PPU modes (only for CPU writes, not PPU writes)
        # OAM (0xFE00-0xFE9F) is blocked during Mode 2 (OAM Search) and Mode 3 (Pixel Transfer)
        # BUT only when LCD is enabled (LCDC bit 7)
        if not self._bypass_ppu_restrictions and 0xFE00 <= address <= 0xFE9F:
            if self._cpu and hasattr(self._cpu, 'ppu'):
                lcdc = self._data[0xFF40]
                if lcdc & 0x80:  # LCD is ON
                    ppu_mode = self._cpu.ppu.current_mode
                    # Mode 2 = OAM Search, Mode 3 = Pixel Transfer
                    if ppu_mode == 2 or ppu_mode == 3:
                        return  # Ignore write

        # Check for VRAM write restrictions during PPU Mode 3 (only for CPU writes, not PPU writes)
        # VRAM (0x8000-0x9FFF) is blocked during Mode 3 (Pixel Transfer)
        # BUT only when LCD is enabled (LCDC bit 7)
        if not self._bypass_ppu_restrictions and 0x8000 <= address <= 0x9FFF:
            if self._cpu and hasattr(self._cpu, 'ppu'):
                lcdc = self._data[0xFF40]
                if lcdc & 0x80:  # LCD is ON
                    ppu_mode = self._cpu.ppu.current_mode
                    if ppu_mode == 3:  # Mode 3 = Pixel Transfer
                        return  # Ignore write

        # P1/JOYP register (0xFF00) - Joypad
        if address == 0xFF00:
            self.joypad.write_p1(value)
            # Store the selection bits in memory too
            self._data[address] = value
            return

        # DIV register (0xFF04) - writing any value resets it to 0 AND the system counter
        if address == 0xFF04:
            self._data[address] = 0x00
            if self._cpu:
                # TIMA counts falling edges of (selected counter bit AND timer enable).
                # Clearing the counter while that bit is 1 is a falling edge too.
                tac = self._data[0xFF07]
                if tac & 0x04 and (self._cpu._system_counter >> (9, 3, 5, 7)[tac & 0x03]) & 1:
                    self._cpu._trigger_timer_tick()
                self._cpu._system_counter = 0
            return

        # TIMA register (0xFF05)
        if address == 0xFF05:
            if self._cpu:
                if self._cpu._tima_reloaded:
                    return                    # reload cycle: TMA wins, the write is lost
                if self._cpu._timer_overflow_cycles > 0:
                    # Writing to TIMA during overflow delay cancels the reload and interrupt
                    self._cpu._timer_overflow_cycles = 0
            self._data[address] = value
            return

        # TMA register (0xFF06): during the reload cycle the new value also goes to TIMA
        if address == 0xFF06:
            self._data[address] = value
            if self._cpu and self._cpu._tima_reloaded:
                self._data[0xFF05] = value
            return

        # TAC register (0xFF07) - obscure behavior on write
        if address == 0xFF07:
            if self._cpu:
                old_tac = self._data[0xFF07]
                new_tac = value

                # Check if old timer was enabled
                old_enabled = (old_tac & 0x04) != 0
                new_enabled = (new_tac & 0x04) != 0

                old_freq = old_tac & 0x03
                new_freq = new_tac & 0x03

                # Bit positions for frequencies
                bit_positions = [9, 3, 5, 7]

                # The falling edge detector monitors: (selected_bit) AND (enable_bit)
                # Get old AND gate output
                if old_enabled:
                    old_bit_pos = bit_positions[old_freq]
                    old_selected_bit = (self._cpu._system_counter >> old_bit_pos) & 1
                    old_and_output = old_selected_bit & 1  # old_enabled is True, so AND with 1
                else:
                    old_and_output = 0  # If disabled, AND output is always 0

                # Get new AND gate output
                if new_enabled:
                    new_bit_pos = bit_positions[new_freq]
                    new_selected_bit = (self._cpu._system_counter >> new_bit_pos) & 1
                    new_and_output = new_selected_bit & 1  # new_enabled is True, so AND with 1
                else:
                    new_and_output = 0  # If disabled, AND output is always 0

                # Falling edge detection: 1 → 0 transition triggers timer tick
                if old_and_output == 1 and new_and_output == 0:
                    self._cpu._trigger_timer_tick()

            self._data[address] = value
            return

        # Boot ROM disable (0xFF50): any write with bit 0 set unmaps the boot ROM.
        # Must come before the unused-register range below, which contains 0xFF50.
        if address == 0xFF50:
            if value & 0x01 and self.boot_rom_enabled:
                self.boot_rom_enabled = False
                self._map_rom()
            return

        # Unused I/O registers - ignore writes
        # These registers don't exist and writes should be ignored
        if address == 0xFF03 or (0xFF08 <= address <= 0xFF0E) or (0xFF4C <= address <= 0xFF7F):
            # Ignore writes to unused registers
            return

        # LY register (0xFF44) - LCD Y-Coordinate (read-only)
        if address == 0xFF44:
            # LY is read-only, ignore writes
            return

        # LCDC register (0xFF40) - LCD Control
        if address == 0xFF40:
            self._data[address] = value
            ppu = getattr(self._cpu, 'ppu', None)
            if ppu:
                ppu.lcdc_written()
            return

        # STAT (0xFF41): only bits 3-6 are writable; mode and LY=LYC flag are read-only
        if address == 0xFF41:
            self._data[address] = (self._data[address] & 0x07) | (value & 0x78)
            ppu = getattr(self._cpu, 'ppu', None)
            if ppu:
                ppu.stat_written()
            return

        # LYC (0xFF45): the LY=LYC comparison is re-checked straight away
        if address == 0xFF45:
            self._data[address] = value
            ppu = getattr(self._cpu, 'ppu', None)
            if ppu:
                ppu.lyc_written()
            return

        # DMA register (0xFF46) - OAM DMA transfer
        if address == 0xFF46:
            # Start DMA transfer from (value << 8) to OAM (0xFE00-0xFE9F)
            # Copies 0xA0 (160) bytes
            self._start_oam_dma(value)
            self._data[address] = value
            return

        # Serial port transfer (test ROM output)
        if address == 0xFF01:
            # Serial data - the character being sent
            self._serial_buffer = value
            self._data[address] = value

        elif address == 0xFF02:
            # Serial control - if bit 7 is set, transfer starts
            if value == 0x81:
                # Transfer requested
                self._serial_output.append(self._serial_buffer)

                # Print character (convert newline, tab, etc.)
                if self._serial_buffer == 0x0A:  # Newline
                    print()
                elif self._serial_buffer == 0x0D:  # Carriage return
                    pass  # Ignore CR, just use LF
                elif 32 <= self._serial_buffer < 127:  # Printable ASCII
                    print(chr(self._serial_buffer), end='', flush=True)
                else:
                    # Non-printable: show as hex for debugging
                    print(f'[{self._serial_buffer:02X}]', end='', flush=True)

                self._data[0xFF01] = 0x00  # Clear data
                self._data[0xFF02] = 0x01  # Mark transfer complete
                return

        self._data[address] = value
    
    """
    def write_byte(self, address: int, value: int) -> None:
        # Write a single byte to memory
        address = validate_word(address)
        value = validate_byte(value)
        self._write_count += 1
        
        # Handle special memory regions
        if address >= MemoryRanges.ECHO_RAM_START and address <= MemoryRanges.ECHO_RAM_END:
            # Echo RAM mirrors C000-DDFF
            mirror_address = address - 0x2000
            self._data[mirror_address] = value
            return
        
        # ROM area (0x0000-0x7FFF) should not be writable in real GB
        # But we'll allow it for testing/development
        if address <= MemoryRanges.ROM_BANK_N_END:
            # In real GB, this would trigger MBC (Memory Bank Controller) logic
            # For now, just write directly
            pass
        
        self._data[address] = value
    """
    
    def read_word(self, address: int) -> int:
        """Read a 16-bit word (little-endian)"""
        # Little-endian: low byte first, high byte second
        low_byte = self.read_byte(address)
        high_byte = self.read_byte(address + 1)
        return (high_byte << 8) | low_byte
    
    def write_word(self, address: int, value: int) -> None:
        """Write a 16-bit word (little-endian)"""
        value = validate_word(value)
        low_byte = value & 0xFF
        high_byte = (value >> 8) & 0xFF
        self.write_byte(address, low_byte)
        self.write_byte(address + 1, high_byte)
    
    def load_rom(self, rom_data: bytes, offset: int = 0) -> None:
        """Load a cartridge ROM (offset 0) or raw bytes at another address."""
        if offset != 0:
            length = min(len(rom_data), 65536 - offset)
            self._data[offset:offset + length] = rom_data[:length]
            return

        self.cartridge = make_cartridge(rom_data)
        self.cartridge_data = self.cartridge.rom
        self._map_rom()
        print(f"Loaded {len(rom_data)} bytes of ROM ({self.cartridge.name}, "
              f"{self.cartridge.rom_banks} ROM banks, {len(self.cartridge.ram)} bytes RAM)")

    def _map_rom(self) -> None:
        """Copy the cartridge's currently selected ROM banks into 0x0000-0x7FFF."""
        cart = self.cartridge
        if not cart:
            return
        b0, bn = cart.bank0 * 0x4000, cart.bankn * 0x4000
        self._data[0x0000:0x4000] = cart.rom[b0:b0 + 0x4000]
        self._data[0x4000:0x8000] = cart.rom[bn:bn + 0x4000]

    def load_rom_file(self, filepath: str) -> None:
        """Load a ROM file from disk"""
        with open(filepath, 'rb') as f:
            rom_data = f.read()
        self.load_rom(rom_data, offset=0)
    
    def dump_region(self, start: int, end: int) -> None:
        """Dump memory region (for debugging)"""
        print(f"\nMemory dump: 0x{start:04X} - 0x{end:04X}")
        for addr in range(start, end + 1, 16):
            hex_bytes = ' '.join(f'{self._data[addr + i]:02X}' for i in range(min(16, end - addr + 1)))
            ascii_chars = ''.join(
                chr(self._data[addr + i]) if 32 <= self._data[addr + i] < 127 else '.'
                for i in range(min(16, end - addr + 1))
            )
            print(f"0x{addr:04X}: {hex_bytes:<48} | {ascii_chars}")
    
    def simulate_boot_rom(self):
        """
        Simulate what the Game Boy boot ROM does:
        1. Clear VRAM (0x8000-0x9FFF) to 0x00
        2. Initialize hardware registers
        3. Set up initial state for game

        This is called instead of running actual boot ROM code
        """
        print("Simulating boot ROM sequence...")

        # Clear VRAM to prevent garbage/stripes
        for addr in range(0x8000, 0xA000):
            self._data[addr] = 0x00

        # Initialize Audio Registers (DMG boot ROM does this)
        self._data[0xFF10] = 0x80  # NR10
        self._data[0xFF11] = 0xBF  # NR11
        self._data[0xFF12] = 0xF3  # NR12
        self._data[0xFF13] = 0xFF  # NR13
        self._data[0xFF14] = 0xBF  # NR14
        self._data[0xFF16] = 0x3F  # NR21
        self._data[0xFF17] = 0x00  # NR22
        self._data[0xFF18] = 0xFF  # NR23
        self._data[0xFF19] = 0xBF  # NR24
        self._data[0xFF1A] = 0x7F  # NR30
        self._data[0xFF1B] = 0xFF  # NR31
        self._data[0xFF1C] = 0x9F  # NR32
        self._data[0xFF1D] = 0xFF  # NR33
        self._data[0xFF1E] = 0xBF  # NR34
        self._data[0xFF20] = 0xFF  # NR41
        self._data[0xFF21] = 0x00  # NR42
        self._data[0xFF22] = 0x00  # NR43
        self._data[0xFF23] = 0xBF  # NR44
        self._data[0xFF24] = 0x77  # NR50
        self._data[0xFF25] = 0xF3  # NR51
        self._data[0xFF26] = 0xF1  # NR52

        # Initialize Video Registers (DMG boot ROM does this)
        self._data[0xFF40] = 0x91  # LCDC: LCD on, BG on
        self._data[0xFF41] = 0x85  # STAT
        self._data[0xFF42] = 0x00  # SCY
        self._data[0xFF43] = 0x00  # SCX
        self._data[0xFF45] = 0x00  # LYC
        self._data[0xFF47] = 0xFC  # BGP (11 11 10 00)
        self._data[0xFF4A] = 0x00  # WY
        self._data[0xFF4B] = 0x00  # WX

        # Initialize I/O Registers
        self.joypad.write_p1(0x00)  # P1 = 0xCF: both button groups selected, nothing pressed
        self._data[0xFF00] = 0x00
        self._data[0xFF01] = 0x00  # SB (Serial data)
        self._data[0xFF02] = 0x7E  # SC (Serial control)
        self._data[0xFF04] = 0xAB  # DIV (Divider, varies but use common value)
        self._data[0xFF05] = 0x00  # TIMA (Timer counter)
        self._data[0xFF06] = 0x00  # TMA (Timer modulo)
        self._data[0xFF07] = 0xF8  # TAC (Timer control)
        self._data[0xFF0F] = 0xE1  # IF (Interrupt flag)
        self._data[0xFFFF] = 0x00  # IE (Interrupt enable)

        # OBP0 and OBP1 remain uninitialized (per Pan Docs)
        # We can set them to reasonable defaults for safety
        # (keeping our previous values of 0xFF is fine)
        self._data[0xFF48] = 0xFF  # OBP0
        self._data[0xFF49] = 0xFF  # OBP1

        # Clear OAM
        for addr in range(0xFE00, 0xFEA0):
            self._data[addr] = 0x00

        # Disable boot ROM and map cartridge
        self.boot_rom_enabled = False
        self._map_rom()

        # Set FF50 to indicate boot complete
        self._data[0xFF50] = 0x01

        ppu = getattr(self._cpu, 'ppu', None)
        if ppu:
            ppu.post_boot_state()

        print("Boot simulation complete - VRAM cleared, all registers initialized")

    def _start_oam_dma(self, value: int):
        """
        Start OAM DMA transfer

        Copies 160 bytes from (value << 8) to OAM (0xFE00-0xFE9F)
        Takes 160 M-cycles (640 T-cycles) during which most memory is inaccessible

        For simplicity, we do an instant copy and advance cycles
        """
        source_addr = value << 8  # Source is XX00-XX9F

        # Copy 160 bytes (0xA0) from source to OAM
        # Bypass PPU restrictions for this direct copy
        old_bypass = self._bypass_ppu_restrictions
        self._bypass_ppu_restrictions = True

        for i in range(0xA0):  # 160 bytes
            if 0xA000 <= source_addr < 0xC000 and self.cartridge:
                source_byte = self.cartridge.read_ram(source_addr + i)
            else:
                source_byte = self._data[source_addr + i]
            self._data[0xFE00 + i] = source_byte

        self._bypass_ppu_restrictions = old_bypass

        # DMA takes 160 M-cycles (640 T-cycles)
        # We could track this with _dma_active flag, but for now do instant transfer
        # and just advance CPU cycles
        if self._cpu:
            # Add the DMA time to total cycles
            # The CPU should essentially "stall" during DMA
            self._cpu.total_cycles += 640

    def get_stats(self) -> dict:
        """Get memory access statistics"""
        return {
            'reads': self._read_count,
            'writes': self._write_count,
            'total_accesses': self._read_count + self._write_count
        }

    def get_serial_output(self) -> str:
        """Get all serial output as a string"""
        return ''.join(chr(b) if 32 <= b < 127 or b in (0x0A, 0x0D) else f'[{b:02X}]'
                       for b in self._serial_output)
    
    def reset(self) -> None:
        """Clear all memory"""
        self._data = bytearray(65536)
        self._read_count = 0
        self._write_count = 0
