"""
Test the actual CRC routine from RAM to verify flag handling
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def test_crc():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Wait for ROM to copy CRC to RAM
    while cpu.total_cycles < 30_000_000:
        if cpu.registers._pc == 0xC000:
            break
        cpu.step()

    # Execute a bit more to let setup complete
    for _ in range(200):
        cpu.step()

    print("Testing CRC routine at 0xC05A...")
    print()

    # Set up test CRC values at 0xFF80-0xFF83
    cpu.memory.write_byte(0xFF80, 0x12)
    cpu.memory.write_byte(0xFF81, 0x34)
    cpu.memory.write_byte(0xFF82, 0x56)
    cpu.memory.write_byte(0xFF83, 0x78)

    # Set up to call CRC
    cpu.registers._pc = 0xC05A
    cpu.registers._sp = 0xDFF0

    print("Initial CRC values:")
    print(f"  0xFF80: 0x{cpu.memory.read_byte(0xFF80):02X}")
    print(f"  0xFF81: 0x{cpu.memory.read_byte(0xFF81):02X}")
    print(f"  0xFF82: 0x{cpu.memory.read_byte(0xFF82):02X}")
    print(f"  0xFF83: 0x{cpu.memory.read_byte(0xFF83):02X}")
    print()

    # Trace through CRC execution
    print("Executing CRC routine...")
    instruction_count = 0
    max_instructions = 500

    while instruction_count < max_instructions:
        pc = cpu.registers._pc

        # Check if we've returned from CRC
        if pc == 0xC093 or (pc < 0xC05A or pc > 0xC092):
            print(f"CRC routine returned after {instruction_count} instructions")
            break

        # Execute one instruction
        cpu.step()
        instruction_count += 1

        # Log key state changes in the loop
        if pc == 0xC068:  # Loop start
            h = cpu.registers._h
            flags = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                    cpu.registers.flags.half_carry, cpu.registers.flags.carry)
            print(f"  Loop iteration, H={h}, Flags: Z={int(flags[0])} N={int(flags[1])} H={int(flags[2])} C={int(flags[3])}")

    print()
    print("Final CRC values:")
    print(f"  0xFF80: 0x{cpu.memory.read_byte(0xFF80):02X}")
    print(f"  0xFF81: 0x{cpu.memory.read_byte(0xFF81):02X}")
    print(f"  0xFF82: 0x{cpu.memory.read_byte(0xFF82):02X}")
    print(f"  0xFF83: 0x{cpu.memory.read_byte(0xFF83):02X}")
    print()

    print(f"Final registers:")
    print(f"  A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X}")
    print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
    print()

    # Run it again with different values and check consistency
    print("Running CRC again with different input...")
    cpu.memory.write_byte(0xFF80, 0xFF)
    cpu.memory.write_byte(0xFF81, 0xFF)
    cpu.memory.write_byte(0xFF82, 0xFF)
    cpu.memory.write_byte(0xFF83, 0xFF)

    cpu.registers._pc = 0xC05A
    cpu.registers._sp = 0xDFF0

    for _ in range(max_instructions):
        if cpu.registers._pc < 0xC05A or cpu.registers._pc > 0xC092:
            break
        cpu.step()

    print(f"CRC with 0xFF input:")
    print(f"  0xFF80: 0x{cpu.memory.read_byte(0xFF80):02X}")
    print(f"  0xFF81: 0x{cpu.memory.read_byte(0xFF81):02X}")
    print(f"  0xFF82: 0x{cpu.memory.read_byte(0xFF82):02X}")
    print(f"  0xFF83: 0x{cpu.memory.read_byte(0xFF83):02X}")

if __name__ == "__main__":
    test_crc()
