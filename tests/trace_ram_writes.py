"""
Trace writes to RAM at 0xC000-0xC100 before JP 0xC000

The test ROM must write code to RAM before jumping there
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Tracing writes to 0xC000-0xC100...")
    print()

    # Monkey-patch memory write to track writes to RAM
    original_write = cpu.memory.write_byte
    ram_writes = []

    def tracked_write(address, value):
        if 0xC000 <= address < 0xC100:
            ram_writes.append((cpu.total_cycles, cpu.registers._pc, address, value))
            if len(ram_writes) <= 100:  # Print first 100 writes
                print(f"[{cpu.total_cycles:>9,}] PC=0x{cpu.registers._pc:04X}: WRITE [0x{address:04X}] = 0x{value:02X}")
        return original_write(address, value)

    cpu.memory.write_byte = tracked_write

    # Run until JP 0xC000
    while cpu.total_cycles < 2_000_000:
        pc_before = cpu.registers._pc

        # Check if we're about to execute JP 0xC000
        if pc_before == 0x0210:
            opcode = cpu.memory.read_byte(0x0210)
            if opcode == 0xC3:  # JP nn
                print()
                print("=" * 80)
                print(f"About to execute JP 0xC000 at PC=0x0210")
                print(f"Total writes to RAM: {len(ram_writes)}")
                print("=" * 80)
                print()

                # Show what's in RAM at 0xC000
                print("RAM contents at 0xC000-0xC020:")
                for addr in range(0xC000, 0xC020):
                    val = cpu.memory.read_byte(addr)
                    print(f"  [0x{addr:04X}] = 0x{val:02X}")

                break

        cpu.step()

    print()
    print("=" * 80)
    print(f"Total RAM writes: {len(ram_writes)}")
    print("=" * 80)

if __name__ == "__main__":
    trace()
