"""Debug script to find where opcode 0xF4 occurs in Super Mario Land ROM"""

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Super Mario Land (World)\Super Mario Land (World).gb"

with open(rom_path, 'rb') as f:
    data = f.read()

print(f"ROM size: {len(data)} bytes")
print(f"\nSearching for opcode 0xF4 in ROM...")

# Find all occurrences of 0xF4
occurrences = []
for i in range(len(data)):
    if data[i] == 0xF4:
        occurrences.append(i)

print(f"Found {len(occurrences)} occurrences of 0xF4:")
for addr in occurrences[:20]:  # Show first 20
    # Show context
    start = max(0, addr - 5)
    end = min(len(data), addr + 6)
    context = ' '.join(f'{data[i]:02X}' for i in range(start, end))
    marker_pos = (addr - start) * 3
    print(f"  0x{addr:04X}: {context}")
    print(f"         {' ' * marker_pos}^^")

# Check what's at 0xCFFB (where error occurred)
print(f"\nByte at 0xCFFB: 0x{data[0xCFFB]:02X}")
print(f"Byte at 0xCFFC: 0x{data[0xCFFC]:02X}")
