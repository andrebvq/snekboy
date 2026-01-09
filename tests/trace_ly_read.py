"""Trace when LDH A,(0x44) is executed and what value it reads"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_ly_read():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("Tracing LDH A,(0x44) instructions...")
    print()

    count = 0
    max_cycles = 20_000

    try:
        while cpu.total_cycles < max_cycles:
            pc_before = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc_before)

            # Check if this is LDH A,(n) at PC=0x0743
            if pc_before == 0x0743 and opcode == 0xF0:
                offset = cpu.memory.read_byte(pc_before + 1)
                ly_value = cpu.memory.read_byte(0xFF00 + offset)
                a_before = cpu.registers._a

                cpu.step()

                a_after = cpu.registers._a

                print(f"[{cpu.total_cycles:>8}] PC=0x{pc_before:04X}: LDH A,(0x{offset:02X})")
                print(f"    Memory[0xFF{offset:02X}] = 0x{ly_value:02X}")
                print(f"    A: 0x{a_before:02X} -> 0x{a_after:02X}")
                print(f"    LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
                print()

                count += 1
                if count > 10:
                    break
            else:
                cpu.step()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_ly_read()
