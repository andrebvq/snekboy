"""
Find where memory at 0xC300 gets written
"""

from src.cpu import CPU

class MonitoredCPU(CPU):
    def __init__(self):
        super().__init__()
        self.c300_write_count = 0

    def step(self):
        # Check for writes to 0xC300-0xC310
        c300_before = tuple(self.memory.read_byte(addr) for addr in range(0xC300, 0xC311))

        # Execute instruction
        result = super().step()

        # Check if changed
        c300_after = tuple(self.memory.read_byte(addr) for addr in range(0xC300, 0xC311))

        if c300_before != c300_after:
            self.c300_write_count += 1
            pc = self.registers._pc
            print(f"\n[{self.total_cycles:>10}] Write to 0xC300 detected (write #{self.c300_write_count})")
            print(f"  PC after write: 0x{pc:04X}")
            print(f"  Before: {' '.join(f'{b:02X}' for b in c300_before[:8])}")
            print(f"  After:  {' '.join(f'{b:02X}' for b in c300_after[:8])}")

            # Try to find what instruction did this by looking back
            # The instruction that wrote this just completed
            print(f"  SP: 0x{self.registers._sp:04X}")
            print(f"  HL: 0x{self.registers.hl:04X}")

        return result

def monitor_writes():
    cpu = MonitoredCPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Monitoring writes to 0xC300...")
    print("=" * 70)

    last_serial = ""
    while cpu.total_cycles < 20_000_000:
        cpu.step()

        # Check serial
        serial = cpu.memory.get_serial_output()
        if serial != last_serial:
            new_chars = serial[len(last_serial):]
            if new_chars.strip():
                print(f"\n[{cpu.total_cycles:>10}] Serial: {repr(new_chars)}")
            last_serial = serial

        # Stop if we've seen enough writes
        if cpu.c300_write_count >= 5:
            print(f"\n[Stopping after {cpu.c300_write_count} writes to 0xC300]")
            break

    print(f"\n{'='*70}")
    print(f"Total writes to 0xC300: {cpu.c300_write_count}")

if __name__ == '__main__':
    monitor_writes()
