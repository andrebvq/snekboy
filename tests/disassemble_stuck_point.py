"""
Disassemble around PC=0xC304 where the emulator gets stuck
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def disassemble():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM (but we only have 32KB, ROM bank 0-1)
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Disassembling around PC=0xC304...")
    print()

    # 0xC304 is in RAM/ROM bank 3 area - outside our loaded ROM!
    # Let's check what's actually at that address in memory

    start_addr = 0xC300
    end_addr = 0xC320

    for addr in range(start_addr, end_addr):
        byte = cpu.memory.read_byte(addr)
        instr_info = OPCODES.get(byte, ["UNKNOWN", 1, 4, (0,0,0,0)])
        instr_name = instr_info[0]

        print(f"0x{addr:04X}: 0x{byte:02X}  {instr_name}")

    print()
    print("=" * 80)
    print(f"NOTE: 0xC000-0xCFFF is Working RAM, not ROM!")
    print(f"If PC=0xC304, the emulator jumped into RAM (likely uninitialized)")
    print("This indicates a control flow bug - PC shouldn't be there")
    print("=" * 80)

if __name__ == "__main__":
    disassemble()
