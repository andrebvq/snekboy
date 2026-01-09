"""
Trace how PC ends up in RAM at 0xC304

Watch for jumps, calls, or returns that take PC into 0xC000-0xCFFF range
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

    print("Tracing PC to find jump into RAM...")
    print()

    last_serial_len = 0
    last_pc = 0

    while cpu.total_cycles < 15_000_000:
        pc_before = cpu.registers._pc

        cpu.step()

        pc_after = cpu.registers._pc

        # Detect if we jumped into RAM (0xC000-0xCFFF)
        if 0xC000 <= pc_after < 0xD000:
            print(f"\n{'='*80}")
            print(f"PC JUMPED INTO RAM!")
            print(f"{'='*80}")
            print(f"Cycle: {cpu.total_cycles:,}")
            print(f"PC before: 0x{pc_before:04X}")
            print(f"PC after:  0x{pc_after:04X}")
            print()

            # Disassemble the instruction that caused the jump
            from src.opcodes import OPCODES
            opcode = cpu.memory.read_byte(pc_before)
            instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
            instr_name = instr_info[0]
            instr_len = instr_info[1]

            instr_bytes = [cpu.memory.read_byte(pc_before + i) for i in range(instr_len)]
            instr_hex = ' '.join([f"{b:02X}" for b in instr_bytes])

            print(f"Instruction at 0x{pc_before:04X}: {instr_hex}  {instr_name}")
            print()

            # Show register state
            print(f"SP: 0x{cpu.registers._sp:04X}")
            print(f"AF: 0x{cpu.registers.af:04X}")
            print(f"BC: 0x{cpu.registers.bc:04X}")
            print(f"DE: 0x{cpu.registers.de:04X}")
            print(f"HL: 0x{cpu.registers.hl:04X}")
            print()

            # Check stack
            print("Top of stack:")
            for i in range(8):
                addr = cpu.registers._sp + i
                val = cpu.memory.read_byte(addr)
                print(f"  [0x{addr:04X}] = 0x{val:02X}")

            return

        last_pc = pc_before

        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>12,}] SERIAL: {repr(serial_str)}")
            last_serial_len = current_serial_len

    print("\nDid not jump into RAM within 15M cycles")

if __name__ == "__main__":
    trace()
