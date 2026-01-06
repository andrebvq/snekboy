"""
Trace test 02's success path to find where BC should become 0x0200
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
print("Running to test 02...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if ' 02' in cpu.memory.get_serial_output():
        print(f"Test 02 started: BC=0x{(cpu.registers._b << 8) | cpu.registers._c:04X}")
        break

# Run to test 02 completion
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if '02:ok' in cpu.memory.get_serial_output():
        bc_at_ok = (cpu.registers._b << 8) | cpu.registers._c
        print(f"Test 02 prints 'ok': BC=0x{bc_at_ok:04X}")
        print(f"  Expected: BC should be 0x0200 (test number 02)")
        print(f"  Actual: BC=0x{bc_at_ok:04X}")
        if bc_at_ok != 0x0200:
            print(f"  ERROR: BC has wrong value!")
        break

# Now trace BC changes until the PUSH BC at 0x02A0 (where test number gets saved)
print("\nTracing BC from 'ok' to POP BC at 0x02A0:")
bc_changes = []

while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    bc_before = (cpu.registers._b << 8) | cpu.registers._c
    
    cpu.step()
    
    bc_after = (cpu.registers._b << 8) | cpu.registers._c
    
    if bc_after != bc_before:
        opcode = rom_data[pc]
        if opcode in OPCODES:
            name = OPCODES[opcode][0]
        else:
            name = f"0x{opcode:02X}"
        bc_changes.append((pc, name, bc_before, bc_after))
    
    # Stop at POP BC where test number is retrieved
    if pc == 0x02A0:
        sp = cpu.registers._sp
        stack_val = (cpu.memory.read_byte(sp+1) << 8) | cpu.memory.read_byte(sp)
        
        print(f"\nReached POP BC at 0x02A0:")
        print(f"  Stack contains: 0x{stack_val:04X}")
        print(f"  Expected: 0x0200 (test number 02)")
        print(f"  This value came from test 02's initialization")
        
        print(f"\nBC changes from 'ok' to POP BC:")
        for change_pc, name, before, after in bc_changes:
            print(f"  PC=0x{change_pc:04X} {name:20s}: BC: 0x{before:04X} -> 0x{after:04X}")
        
        break

print("\n" + "="*80)
print("ANALYSIS:")
print("The bug is that test 02 starts with BC=0x01xx but should start with BC=0x02xx")
print("This means test 01's completion didn't set up the correct value for test 02")
