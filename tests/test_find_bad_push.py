"""
Find where 0x2060 gets pushed onto the stack for test 02
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 02 start
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if ' 02' in cpu.memory.get_serial_output():
        break

# Track all PUSH operations until we find one that pushes something close to 0x2060
print("Looking for PUSH operations in test 02...")
pushes = []

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)
    
    # Check for PUSH operations
    if opcode in [0xC5, 0xD5, 0xE5, 0xF5]:  # PUSH BC, DE, HL, AF
        reg_name = {0xC5: 'BC', 0xD5: 'DE', 0xE5: 'HL', 0xF5: 'AF'}[opcode]
        
        # Get register value
        if opcode == 0xC5:
            val = (cpu.registers._b << 8) | cpu.registers._c
        elif opcode == 0xD5:
            val = (cpu.registers._d << 8) | cpu.registers._e
        elif opcode == 0xE5:
            val = cpu.registers.hl
        else:  # AF
            val = (cpu.registers._a << 8) | (
                (int(cpu.registers.flags.zero) << 7) |
                (int(cpu.registers.flags.subtract) << 6) |
                (int(cpu.registers.flags.half_carry) << 5) |
                (int(cpu.registers.flags.carry) << 4)
            )
        
        sp = cpu.registers._sp
        pushes.append((cpu.total_cycles, pc, reg_name, val, sp))
        
        # If this push writes to where the POP will read from
        # POP BC at 0x02A0 reads from SP, and we know SP will be around 0xD64C at that time
        if val == 0x2060:
            print(f"\nFound PUSH that writes 0x2060!")
            print(f"  Cycle: {cpu.total_cycles:,}")
            print(f"  PC: 0x{pc:04X}")
            print(f"  Instruction: PUSH {reg_name}")
            print(f"  Value: 0x{val:04X}")
            print(f"  SP before: 0x{sp:04X}")
            print(f"  Will write to: 0x{sp-2:04X}")
    
    cpu.step()
    
    # Stop after test 02 completes
    if '02:ok' in cpu.memory.get_serial_output():
        break

print(f"\nTotal PUSH operations: {len(pushes)}")
print(f"\nLast 10 pushes before test 02 'ok':")
for cycle, pc, reg, val, sp in pushes[-10:]:
    marker = " <<<" if val == 0x2060 else ""
    print(f"  [{cycle:>10,}] PC=0x{pc:04X} PUSH {reg:2s} = 0x{val:04X} at SP=0x{sp:04X}{marker}")
