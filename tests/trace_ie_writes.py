"""
Trace all writes to IE register (0xFFFF)

The test ROM should enable interrupts by writing to IE.
Let's see if and when this happens.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_ie():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM correctly - don't overwrite I/O registers!
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Loaded ROM correctly (0x0000-0x7FFF only)")
    print(f"IE after ROM load: 0x{cpu.memory.read_byte(0xFFFF):02X}")
    print()
    print("Tracing writes to IE (0xFFFF)...")
    print()

    # Monkey-patch memory write to detect IE writes
    original_write = cpu.memory.write_byte
    ie_writes = []

    def tracked_write(address, value):
        if address == 0xFFFF:
            ie_writes.append((cpu.total_cycles, cpu.registers._pc, value))
            print(f"[{cpu.total_cycles:>9,}] PC=0x{cpu.registers._pc:04X}: WRITE IE = 0x{value:02X}")
        return original_write(address, value)

    cpu.memory.write_byte = tracked_write

    max_cycles = 1_000_000
    last_serial_len = 0

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()

            # Check serial
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes)
                print()
                print(f"[{cpu.total_cycles:>9,}] >>> SERIAL: {repr(new_str)}")
                print()
                last_serial_len = current_serial_len

    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total IE writes: {len(ie_writes)}")
    print(f"Final IE value: 0x{cpu.memory.read_byte(0xFFFF):02X}")
    print("=" * 80)

if __name__ == "__main__":
    trace_ie()
