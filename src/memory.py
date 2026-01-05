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

import numpy as np
from typing import Optional
from src.utils import validate_byte, validate_word, MemoryRanges

class Memory:
    """Game Boy Memory Management Unit"""
    
    def __init__(self):
        # 64KB address space (0x0000 to 0xFFFF)
        self._data = np.zeros(65536, dtype=np.uint8)
        
        # Optional: Track read/write for debugging
        self._read_count = 0
        self._write_count = 0
    
    def read_byte(self, address: int) -> int:
        """Read a single byte from memory"""
        address = validate_word(address)  # Ensure 16-bit address
        self._read_count += 1
        
        # Handle special memory regions
        if address >= MemoryRanges.ECHO_RAM_START and address <= MemoryRanges.ECHO_RAM_END:
            # Echo RAM mirrors C000-DDFF
            mirror_address = address - 0x2000
            return int(self._data[mirror_address])
        
        return int(self._data[address])
    
    def write_byte(self, address: int, value: int) -> None:
        """Write a single byte to memory"""
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
        """Load ROM data into memory at specified offset"""
        rom_array = np.frombuffer(rom_data, dtype=np.uint8)
        length = min(len(rom_array), 65536 - offset)
        self._data[offset:offset + length] = rom_array[:length]
        print(f"Loaded {length} bytes of ROM at address 0x{offset:04X}")
    
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
    
    def get_stats(self) -> dict:
        """Get memory access statistics"""
        return {
            'reads': self._read_count,
            'writes': self._write_count,
            'total_accesses': self._read_count + self._write_count
        }
    
    def reset(self) -> None:
        """Clear all memory"""
        self._data.fill(0)
        self._read_count = 0
        self._write_count = 0
