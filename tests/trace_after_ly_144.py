"""
Trace execution after LY reaches 144
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_after_ly_144():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until LY reaches 144...")

    # Run until LY == 144
    while cpu.total_cycles < 1_000_000:
        ly = cpu.memory.read_byte(0xFF44)
        if ly == 144:
            print(f"LY reached 144 at cycle {cpu.total_cycles:,}")
            print(f"PC: 0x{cpu.registers._pc:04X}")
            print()
            break
        cpu.step()

    # Now trace the next 50 instructions
    print("Tracing next 50 instructions:")
    print("=" * 80)

    for i in range(50):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)
        ly = cpu.memory.read_byte(0xFF44)

        # Get instruction name
        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            instr_name = OPCODES.get(opcode, ["??"])[0]

        # Execute
        cpu.step()
        pc_after = cpu.registers._pc

        # Log
        print(f"[{i+1:>2}] 0x{pc:04X}: {instr_name:20} -> PC=0x{pc_after:04X}  LY={ly:>3}")

        # Check if we exit the VBlank wait loop
        if pc == 0x0749:  # POP BC after exiting loop
            print("\n*** Exited VBlank wait loop! ***\n")

    print("=" * 80)

if __name__ == "__main__":
    trace_after_ly_144()
