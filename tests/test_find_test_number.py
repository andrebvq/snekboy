"""
Find where the test number gets loaded into B
The test framework must load test number somewhere
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 03 start
print("Running to test 03...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started")
        print(f"B = 0x{cpu.registers._b:02X}")
        print(f"C = 0x{cpu.registers._c:02X}")
        print(f"BC = 0x{cpu.registers._b:04X}{cpu.registers._c:02X}")
        break

# Now let's trace back to see where test number comes from
# Run from beginning and look for where test numbers are stored
print("\nLooking for where test numbers are initialized...")

cpu2 = CPU()
for i, byte in enumerate(rom_data):
    cpu2.memory._data[i] = byte

# Look for memory addresses that might contain test numbers
# Test numbers would be: 01, 02, 03, etc
print("\nScanning ROM for test number table...")
for addr in range(0x0000, 0x8000):
    # Look for sequences like 01,02,03 or just single bytes
    if rom_data[addr] == 0x01 and addr + 2 < len(rom_data):
        if rom_data[addr+1] == 0x02 and rom_data[addr+2] == 0x03:
            print(f"Found 01,02,03 sequence at 0x{addr:04X}")

# Let's also check what's at the addresses referenced in the test code
print("\nChecking key addresses:")
print(f"  Memory at 0xD61B-0xD61D (where DE points during init):")
for i in range(3):
    val = rom_data[0xD61B + i] if 0xD61B + i < len(rom_data) else 0
    print(f"    [0x{0xD61B+i:04X}] = 0x{val:02X}")
