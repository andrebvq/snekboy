"""Disassemble around PC=0x0846 where B is decremented to 0"""
import sys
sys.path.insert(0, '.')

def disassemble_area():
    """Read and show bytes around 0x0846"""
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()

    start = 0x0840
    end = 0x0850

    print("=" * 80)
    print(f"ROM BYTES FROM 0x{start:04X} TO 0x{end:04X}")
    print("=" * 80)

    for addr in range(start, end):
        byte = rom_data[addr]
        print(f"0x{addr:04X}: 0x{byte:02X}  ({byte:3d})  {chr(byte) if 32 <= byte < 127 else '?'}")

    print()
    print("=" * 80)
    print("COMMON OPCODES:")
    print("=" * 80)
    print("0x05 = DEC B")
    print("0x20 = JR NZ,n")
    print("0x06 = LD B,n")
    print("0xC9 = RET")
    print("0xCD = CALL nn")
    print("=" * 80)

if __name__ == "__main__":
    disassemble_area()
