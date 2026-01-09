"""
Trace all writes to memory address 0xC35C to see what gets written there
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.memory import Memory

# Monkey-patch Memory class to track writes
original_write_byte = Memory.write_byte

write_log = []

def tracked_write_byte(self, address, value):
    if 0xC350 <= address <= 0xC370:  # Track writes around 0xC35C
        import traceback
        write_log.append({
            'address': address,
            'value': value,
            'pc': self._cpu.registers._pc if hasattr(self, '_cpu') else 0,
            'cycle': self._cpu.total_cycles if hasattr(self, '_cpu') else 0
        })
    return original_write_byte(self, address, value)

Memory.write_byte = tracked_write_byte

def trace_writes():
    cpu = CPU()
    cpu.memory._cpu = cpu  # Backlink for tracking

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Tracking writes to 0xC350-0xC370...")
    print()

    # Run until PC reaches 0xC24C (where the problematic CALL is)
    while cpu.total_cycles < 30_000_000 and cpu.registers._pc != 0xC24C:
        cpu.step()

    print(f"Reached PC=0xC24C at cycle {cpu.total_cycles:,}")
    print()
    print("Writes to 0xC350-0xC370:")
    print("=" * 80)

    for entry in write_log:
        print(f"[{entry['cycle']:>10,}] PC=0x{entry['pc']:04X} wrote 0x{entry['value']:02X} to 0x{entry['address']:04X}")

    print("=" * 80)
    print()
    print(f"Total writes to this region: {len(write_log)}")
    print()

    # Show final memory state
    print("Final memory state at 0xC350-0xC370:")
    for addr in range(0xC350, 0xC371):
        value = cpu.memory.read_byte(addr)
        marker = " <-- CALL target" if addr == 0xC35C else ""
        print(f"  0x{addr:04X}: 0x{value:02X}{marker}")

if __name__ == "__main__":
    trace_writes()
