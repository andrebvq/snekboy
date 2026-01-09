"""
Disassemble the code around 0xC304 to see what's there
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def disasm_area():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until test 03 starts
    last_serial_len = 0
    while cpu.total_cycles < 30_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if '03' in full_serial:
                break
            last_serial_len = current_serial_len
        cpu.step()

    # Let it run a bit more to populate RAM
    for _ in range(100000):
        cpu.step()

    print("Disassembly around 0xC304:")
    print("=" * 80)

    for addr in range(0xC2F0, 0xC320):
        op = cpu.memory.read_byte(addr)
        byte1 = cpu.memory.read_byte(addr + 1)
        byte2 = cpu.memory.read_byte(addr + 2)

        op_info = OPCODES.get(op, ["??", 0, 0])
        op_name = op_info[0]

        # Format based on instruction size
        if op == 0xCB:
            cb_op = byte1
            print(f"  0x{addr:04X}: {op:02X} {byte1:02X}     CB {byte1:02X}")
        elif op_name in ["LD r,n", "LD (HL),n", "ADD A,n", "ADC A,n", "SUB n", "SBC A,n", "AND n", "XOR n", "OR n", "CP n", "JR n", "JR NZ,n", "JR Z,n", "JR NC,n", "JR C,n"]:
            print(f"  0x{addr:04X}: {op:02X} {byte1:02X}     {op_name} ${byte1:02X}")
        elif op_name in ["LD r,nn", "LD (nn),SP", "LD nn,A", "LD A,(nn)", "JP nn", "JP NZ,nn", "JP Z,nn", "JP NC,nn", "JP C,nn", "CALL nn", "CALL NZ,nn", "CALL Z,nn", "CALL NC,nn", "CALL C,nn"]:
            word = byte1 | (byte2 << 8)
            print(f"  0x{addr:04X}: {op:02X} {byte1:02X} {byte2:02X}  {op_name} ${word:04X}")
        else:
            print(f"  0x{addr:04X}: {op:02X} {byte1:02X} {byte2:02X}  {op_name}")

        # Highlight 0xC304
        if addr == 0xC304:
            print("         ^^^ STUCK HERE ^^^")

    print()
    print("=" * 80)

if __name__ == "__main__":
    disasm_area()
