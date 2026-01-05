"""
Trace through the actual delay loop
"""

from src.cpu import CPU

def test_delay_loop():
    cpu = CPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom = f.read()
    for i, b in enumerate(rom):
        cpu.memory._data[i] = b

    print("Simulating delay loop at 0x0213-0x0215")
    print("=" * 60)

    # Set PC to start of loop (actually need to start a bit earlier to load A)
    # Let me find where A gets loaded first
    print("\nInstructions before the loop:")
    for addr in range(0x0200, 0x0218):
        opcode = cpu.memory.read_byte(addr)
        try:
            from src.opcodes import OPCODES
            if opcode in OPCODES:
                name = OPCODES[opcode][0]
                print(f"  0x{addr:04X}: 0x{opcode:02X} - {name}")
            else:
                print(f"  0x{addr:04X}: 0x{opcode:02X}")
        except:
            print(f"  0x{addr:04X}: 0x{opcode:02X}")

if __name__ == '__main__':
    test_delay_loop()
