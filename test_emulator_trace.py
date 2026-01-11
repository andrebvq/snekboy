"""Test if emulator creates trace file"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# First, clean up any existing trace file
trace_file = "tracing/tracing.txt"
if os.path.exists(trace_file):
    os.remove(trace_file)
    print(f"Removed existing {trace_file}")

print("Testing emulator trace file creation...")
print("="*70)

# Try to import and create emulator
try:
    from src.emulator import Emulator

    print("Creating emulator with tracing enabled...")
    # Don't pass a ROM, just test initialization
    emu = Emulator(rom_path=None, enable_tracing=True)

    print(f"✓ Emulator created")
    print(f"✓ Tracer enabled: {emu.enable_tracing}")
    print(f"✓ Trace file path: {emu.trace_file}")

    # Log a test message
    emu.tracer.log("TEST: Emulator initialized successfully")

    # Check if file exists
    if os.path.exists(trace_file):
        print(f"✓ Trace file created: {trace_file}")
        with open(trace_file, 'r') as f:
            content = f.read()
            print(f"✓ File size: {len(content)} bytes")
            print("\nFile contents:")
            print("-"*70)
            print(content)
            print("-"*70)
    else:
        print(f"✗ ERROR: Trace file not found: {trace_file}")

    # Clean up
    emu.tracer.close()
    emu.display.close()

    print("\n✓ SUCCESS - Tracer is working!")

except Exception as e:
    print(f"\n✗ ERROR during emulator creation:")
    print(f"  {type(e).__name__}: {e}")

    import traceback
    traceback.print_exc()

    # Check if trace file was created anyway
    if os.path.exists(trace_file):
        print(f"\n✓ Despite error, trace file WAS created: {trace_file}")
        with open(trace_file, 'r') as f:
            print("\nFile contents:")
            print("-"*70)
            print(f.read())
            print("-"*70)
    else:
        print(f"\n✗ Trace file was NOT created: {trace_file}")
