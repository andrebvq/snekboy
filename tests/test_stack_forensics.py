"""
Forensic analysis of stack state before POP BC at 0x02A0
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 02 completion
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if '02:ok' in cpu.memory.get_serial_output():
        break

# Now run to just before POP BC at 0x02A0
while cpu.total_cycles < 15_000_000:
    if cpu.registers._pc == 0x02A0:
        sp = cpu.registers._sp
        
        print(f"At POP BC (0x02A0):")
        print(f"  SP = 0x{sp:04X}")
        print(f"\nStack contents:")
        for i in range(10):
            addr = sp + i
            val = cpu.memory.read_byte(addr)
            marker = " <- SP" if i == 0 else " <- SP+1" if i == 1 else ""
            print(f"  [0x{addr:04X}] = 0x{val:02X}{marker}")
        
        # The value that will be popped
        c_val = cpu.memory.read_byte(sp)
        b_val = cpu.memory.read_byte(sp + 1)
        bc_val = (b_val << 8) | c_val
        
        print(f"\nPOP BC will load:")
        print(f"  C = 0x{c_val:02X} (from [0x{sp:04X}])")
        print(f"  B = 0x{b_val:02X} (from [0x{sp+1:04X}])")
        print(f"  BC = 0x{bc_val:04X}")
        print(f"\nExpected: BC = 0x0200")
        print(f"Actual:   BC = 0x{bc_val:04X}")
        
        break
    cpu.step()
