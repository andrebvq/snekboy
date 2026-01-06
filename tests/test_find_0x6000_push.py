"""
Find where 0x6000 gets pushed onto the stack during test 02
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 02
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if ' 02' in cpu.memory.get_serial_output():
        print("Test 02 started, tracking PUSH operations...")
        break

# Track all PUSH operations looking for 0x6000
found_pushes = []

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)
    
    # Check for PUSH operations
    if opcode in [0xC5, 0xD5, 0xE5, 0xF5]:
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
        
        if val == 0x6000:
            found_pushes.append((cpu.total_cycles, pc, reg_name, sp))
            print(f"\nFound PUSH {reg_name} = 0x6000 at PC=0x{pc:04X}, SP=0x{sp:04X}")
    
    cpu.step()
    
    if '02:ok' in cpu.memory.get_serial_output():
        print(f"\nTest 02 completed")
        break

print(f"\nTotal pushes of 0x6000: {len(found_pushes)}")

if found_pushes:
    print(f"\nThese PUSH operations wrote 0x6000 to the stack:")
    for cycle, pc, reg, sp in found_pushes:
        print(f"  Cycle {cycle:,}: PC=0x{pc:04X} PUSH {reg} at SP=0x{sp:04X} -> writes to 0x{sp-2:04X}")
