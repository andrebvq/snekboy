"""
Compare B register between test 01->02 and test 02->03 transitions
to find where the increment should happen
"""

from src.cpu import CPU

cpu = CPU()
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

print("="*80)
print("ANALYZING TEST 01 -> TEST 02 TRANSITION")
print("="*80)

# Run to test 01 completion
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if '01:ok' in cpu.memory.get_serial_output():
        b_after_01 = cpu.registers._b
        print(f"\nTest 01 completed:")
        print(f"  B = 0x{b_after_01:02X}")
        break

# Track B until we hit the encoding at 0x064B (second LD A,B)
b_values_01_to_02 = []
while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    b_before = cpu.registers._b
    
    cpu.step()
    
    b_after = cpu.registers._b
    
    if b_after != b_before:
        b_values_01_to_02.append((cpu.total_cycles, pc, b_before, b_after))
    
    if pc == 0x064B:  # Second LD A,B in encoding
        print(f"\nAt encoding (0x064B) for test 02:")
        print(f"  B = 0x{b_after:02X}")
        print(f"  Expected: 0x02")
        
        if b_after == 0x02:
            print(f"  CORRECT!")
        
        print(f"\nB changes during transition (last 10):")
        for cycle, change_pc, before, after in b_values_01_to_02[-10:]:
            print(f"  PC=0x{change_pc:04X}: B: 0x{before:02X} -> 0x{after:02X}")
        break

print("\n" + "="*80)
print("ANALYZING TEST 02 -> TEST 03 TRANSITION")
print("="*80)

# Continue to test 02 completion
while cpu.total_cycles < 15_000_000:
    cpu.step()
    if '02:ok' in cpu.memory.get_serial_output():
        b_after_02 = cpu.registers._b
        print(f"\nTest 02 completed:")
        print(f"  B = 0x{b_after_02:02X}")
        break

# Track B until encoding at 0x064B
b_values_02_to_03 = []
while cpu.total_cycles < 15_000_000:
    pc = cpu.registers._pc
    b_before = cpu.registers._b
    
    cpu.step()
    
    b_after = cpu.registers._b
    
    if b_after != b_before:
        b_values_02_to_03.append((cpu.total_cycles, pc, b_before, b_after))
    
    if pc == 0x064B:
        print(f"\nAt encoding (0x064B) for test 03:")
        print(f"  B = 0x{b_after:02X}")
        print(f"  Expected: 0x03")
        
        if b_after != 0x03:
            print(f"  ERROR: B should be 0x03!")
        
        print(f"\nB changes during transition (last 10):")
        for cycle, change_pc, before, after in b_values_02_to_03[-10:]:
            print(f"  PC=0x{change_pc:04X}: B: 0x{before:02X} -> 0x{after:02X}")
        break

print("\n" + "="*80)
print("COMPARISON")
print("="*80)

print(f"\nTest 01->02: B ends at 0x{b_values_01_to_02[-1][3]:02X}")
print(f"Test 02->03: B ends at 0x{b_values_02_to_03[-1][3]:02X}")

print(f"\nLooking for differences in the transition patterns...")

# Find common pattern
print(f"\nTest 01->02 had {len(b_values_01_to_02)} B changes")
print(f"Test 02->03 had {len(b_values_02_to_03)} B changes")

# Check if there's a missing INC B
has_inc_01_02 = any(after == before + 1 for _, _, before, after in b_values_01_to_02)
has_inc_02_03 = any(after == before + 1 for _, _, before, after in b_values_02_to_03)

print(f"\nTest 01->02 has INC B: {has_inc_01_02}")
print(f"Test 02->03 has INC B: {has_inc_02_03}")
