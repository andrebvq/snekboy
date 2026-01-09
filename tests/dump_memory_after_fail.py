"""
Dump relevant memory areas after test 03 fails
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def dump_after_fail():
    cpu = CPU()

    rom_path = "test_roms/03-op_sp_hl.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until "Failed" appears
    last_serial_len = 0
    while cpu.total_cycles < 50_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if 'Failed' in current_serial:
                break
            last_serial_len = current_serial_len
        cpu.step()

    print("Test failed!")
    print(f"Cycle: {cpu.total_cycles:,}")
    print()

    # Dump CPU state
    def get_f_register(flags):
        f = 0
        if flags.zero: f |= 0x80
        if flags.subtract: f |= 0x40
        if flags.half_carry: f |= 0x20
        if flags.carry: f |= 0x10
        return f

    print("CPU State:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
    print()

    # Dump work RAM area ($C000-$C100)
    print("Work RAM ($C000-$C07F):")
    for addr in range(0xC000, 0xC080, 16):
        bytes_str = ' '.join(f'{cpu.memory.read_byte(addr + i):02X}' for i in range(16))
        print(f"  0x{addr:04X}: {bytes_str}")

    print()

    # Dump high RAM ($FF80-$FFFF)
    print("High RAM ($FF80-$FFFF):")
    for addr in range(0xFF80, 0x10000, 16):
        bytes_str = ' '.join(f'{cpu.memory.read_byte(addr + i):02X}' for i in range(16))
        print(f"  0x{addr:04X}: {bytes_str}")

    print()

    # Check specific addresses used by Blargg tests
    print("Blargg test variables:")
    print(f"  Test number [0xA000]: 0x{cpu.memory.read_byte(0xA000):02X}")
    print(f"  Status [0xA001]: 0x{cpu.memory.read_byte(0xA001):02X}")

    # Check CRC area
    print()
    print("CRC area ($FF83-$FF86):")
    for addr in range(0xFF83, 0xFF87):
        val = cpu.memory.read_byte(addr)
        print(f"  [0x{addr:04X}] = 0x{val:02X}")

if __name__ == "__main__":
    dump_after_fail()
