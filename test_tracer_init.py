"""Test if tracer initializes correctly when emulator starts"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test what happens during emulator init
def test_tracer_path():
    """Test the tracer path logic from emulator"""

    # Simulate what emulator.__init__ does
    trace_file = r"C:\Users\andre\OneDrive\Desktop\projects\snekboy\tracing\tracing.txt"
    enable_tracing = True

    # This is what emulator does
    import os
    trace_path = os.path.abspath(trace_file)

    print(f"Trace file parameter: {trace_file}")
    print(f"Absolute trace path: {trace_path}")
    print(f"Directory: {os.path.dirname(trace_path)}")
    print(f"Directory exists: {os.path.exists(os.path.dirname(trace_path))}")

    # Now create tracer
    from src.tracer import Tracer
    tracer = Tracer(trace_path, enabled=enable_tracing)

    print(f"Tracer created successfully")
    print(f"Tracer file object: {tracer.file}")
    print(f"File closed: {tracer.file.closed if tracer.file else 'No file'}")

    # Try to log something
    tracer.log("Test message from tracer init test")
    tracer.log("If you see this, tracer is working!")

    # Check if file exists before closing
    print(f"File exists before close: {os.path.exists(trace_path)}")

    tracer.close()

    print(f"File exists after close: {os.path.exists(trace_path)}")
    print(f"\nSUCCESS - Check {trace_path}")

if __name__ == "__main__":
    test_tracer_path()
