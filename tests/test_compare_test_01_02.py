"""
Compare test 01 and test 02 initialization to understand the pattern
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

print("="*80)
print("TEST 01 ANALYSIS")
print("="*80)

# Run to test 01 start
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if ' 01' in cpu.memory.get_serial_output():
        print(f"\nTest 01 started")
        break

# Run to POP BC at 0x02A0 (where test number is loaded)
while cpu.total_cycles < 15_000_000:
    if cpu.registers._pc == 0x02A0:
        sp = cpu.registers._sp
        bc_from_stack = (cpu.memory.read_byte(sp+1) << 8) | cpu.memory.read_byte(sp)
        print(f"  At POP BC (0x02A0): Stack has 0x{bc_from_stack:04X}")
        print(f"  Expected: 0x0100 for test 01")
        cpu.step()
        bc_after = (cpu.registers._b << 8) | cpu.registers._c
        print(f"  After POP: BC = 0x{bc_after:04X}")
        break
    cpu.step()

# Run to test 01 completion
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if '01:ok' in cpu.memory.get_serial_output():
        bc_at_ok = (cpu.registers._b << 8) | cpu.registers._c
        print(f"\nTest 01 completes: BC = 0x{bc_at_ok:04X}")
        break

print("\n" + "="*80)
print("TEST 02 ANALYSIS")
print("="*80)

# Run to test 02 start
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if ' 02' in cpu.memory.get_serial_output() and '01:ok' in cpu.memory.get_serial_output():
        print(f"\nTest 02 started")
        break

# Run to POP BC at 0x02A0
while cpu.total_cycles < 15_000_000:
    if cpu.registers._pc == 0x02A0:
        sp = cpu.registers._sp
        bc_from_stack = (cpu.memory.read_byte(sp+1) << 8) | cpu.memory.read_byte(sp)
        print(f"  At POP BC (0x02A0): Stack has 0x{bc_from_stack:04X}")
        print(f"  Expected: 0x0200 for test 02")
        cpu.step()
        bc_after = (cpu.registers._b << 8) | cpu.registers._c
        print(f"  After POP: BC = 0x{bc_after:04X}")
        
        if bc_from_stack != 0x0200:
            print(f"\n  ERROR: Stack should have 0x0200 but has 0x{bc_from_stack:04X}")
            print(f"  This means test 01 didn't push the correct value for test 02")
        break
    cpu.step()

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Test 01 should push 0x0200 onto stack for test 02 to use")
print("But it's pushing 0x0100 instead (test 01's own number)")
print("This pattern repeats: test 02 pushes 0x0100 for test 03 instead of 0x0300")
