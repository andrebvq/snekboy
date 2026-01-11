"""Diagnose why trace file isn't being created"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("TRACE FILE DIAGNOSTIC")
print("="*70)

# Check if file exists before
trace_file = "tracing/tracing.txt"
abs_trace = os.path.abspath(trace_file)

print(f"\nExpected trace file location:")
print(f"  Relative: {trace_file}")
print(f"  Absolute: {abs_trace}")
print(f"  Exists before: {os.path.exists(abs_trace)}")

# Now simulate what emulator.py does when called with a ROM
print("\n" + "-"*70)
print("Simulating emulator initialization...")
print("-"*70)

from src.emulator import Emulator

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

# Create emulator just like the __main__ block does
print(f"\nCreating emulator with ROM: {TETRIS_ROM}")
print(f"Enable tracing: True")

emu = Emulator(TETRIS_ROM, enable_tracing=True)

print(f"\n✓ Emulator created successfully")
print(f"  Tracer enabled: {emu.enable_tracing}")
print(f"  Tracer file path: {emu.trace_file}")
print(f"  Tracer object: {emu.tracer}")
print(f"  File handle: {emu.tracer.file}")
print(f"  File handle closed: {emu.tracer.file.closed if emu.tracer.file else 'N/A'}")

# Check if the file was created
print(f"\n✓ File exists after emulator init: {os.path.exists(emu.trace_file)}")

if os.path.exists(emu.trace_file):
    file_size = os.path.getsize(emu.trace_file)
    print(f"✓ File size: {file_size} bytes")

    if file_size > 0:
        print(f"\n✓ SUCCESS - Trace file is being created and written to!")
        print(f"\nFile location: {emu.trace_file}")
        print("\nFirst 500 characters:")
        print("-"*70)
        with open(emu.trace_file, 'r') as f:
            print(f.read(500))
        print("-"*70)
    else:
        print(f"\n✗ WARNING - File exists but is empty (0 bytes)")
else:
    print(f"\n✗ ERROR - File not created at: {emu.trace_file}")

# Clean up
emu.tracer.close()
emu.display.close()

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
