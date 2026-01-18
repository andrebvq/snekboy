# Test Suite Organization

## Quick Start

### Run Unit Tests
```bash
# Run all unit tests
python tests/run_unit_tests.py all

# Run specific unit test
python tests/run_unit_tests.py cpu
python tests/run_unit_tests.py timer
python tests/run_unit_tests.py joypad
```

### Run Blargg Tests
```bash
# Run Blargg cpu_instrs test ROM
python tests/run_blargg_tests.py

# Run with debug output
python tests/run_blargg_tests.py debug
```

### Run Diagnostic Tools
```bash
# Check Tetris game state
python tests/diagnostic_tools.py tetris_state

# Trace interrupt behavior
python tests/diagnostic_tools.py trace_interrupts

# Monitor VBlank interrupts
python tests/diagnostic_tools.py check_vblank

# Analyze polling loops
python tests/diagnostic_tools.py polling_loop
```

---

## Test Categories

### 1. Organized Test Suites (USE THESE)

#### `run_unit_tests.py`
Runs unit tests for individual components:
- CPU instruction execution
- Memory system
- Timer (DIV, TIMA, TAC)
- Interrupts (EI, DI, RETI)
- Joypad
- PPU basics

#### `run_blargg_tests.py`
Runs Blargg cpu_instrs test ROM suite:
- Tests 01-11 (currently 01-02 pass)
- Standard test ROM for CPU verification
- Serial output capture

#### `diagnostic_tools.py`
Interactive debugging tools:
- `tetris_state` - Full state dump at specific cycle
- `trace_interrupts` - Track IME changes
- `check_vblank` - Monitor VBlank interrupts
- `polling_loop` - Analyze stuck loops

---

### 2. Legacy Individual Tests (Historical Reference)

The `tests/` directory contains many individual test files from debugging sessions.
These are kept for reference but should NOT be used for regular testing.

**Categories of legacy tests:**

#### Blargg Test 03 Investigation
Files investigating the test 03 timeout issue:
- `test_03_*.py` - Various test 03 specific tests
- `test_trace_03_*.py` - Detailed traces of test 03 execution
- `test_blargg_03_*.py` - Instrumented test 03 runs

#### Timer Debugging
Files from timer system debugging:
- `test_timer*.py` - Timer behavior tests
- `test_div_*.py` - DIV register tests
- `test_tac_*.py` - TAC register tests
- `test_tma_*.py` - TMA reload tests
- `compare_timer_approaches.py` - Timer implementation comparison

#### Instruction Debugging
Files testing specific instructions:
- `test_add_*.py` - ADD instruction variants
- `test_sub_*.py` - SUB instruction tests
- `test_ld.py` - Load instruction tests
- `test_pop_af.py` - POP AF flag masking

#### Stack/SP Debugging
Files investigating stack pointer issues:
- `test_sp_hl_*.py` - SP and HL interaction tests
- `test_add_sp_*.py` - ADD SP,e instruction tests
- `test_find_*_push.py` - Stack operation traces

#### Tetris Game Debugging
Files from Tetris-specific debugging:
- `debug_tetris.py` - Tetris execution tracing
- `wait_for_*.py` - Wait for specific game states
- `check_polling_loop.py` - Polling loop analysis
- `diagnose_stuck_state.py` - Comprehensive state dump
- `trace_*_isr.py` - Interrupt handler traces
- `find_vblank_handler.py` - VBlank handler location

#### General Debugging Tools
Miscellaneous debugging scripts:
- `analyze_*.py` - Loop and code analysis
- `trace_*.py` - Execution tracing
- `verify_*.py` - Verification of specific behaviors
- `where_is_cpu.py` - CPU state inspection

---

## Creating New Tests

### Unit Test Template
```python
"""
Test description
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.cpu import CPU

def test_feature():
    cpu = CPU()
    # ... test code ...
    assert condition, "Error message"
    print("[PASS] Test passed")

if __name__ == "__main__":
    test_feature()
```

### Add to run_unit_tests.py
```python
UNIT_TESTS = {
    # ...
    "new_test": "tests/test_new_feature.py",
}
```

---

## Test ROM Downloads

Download Blargg test ROMs:
```bash
python tests/download_test_roms.py
```

This creates `test_roms/` directory with:
- `cpu_instrs.gb` - Complete CPU instruction test suite
- Individual test ROMs (01-special.gb, 02-interrupts.gb, etc.)

---

## Current Test Status

### Passing Tests
- Test 01: Special instructions
- Test 02: Interrupts
- All unit tests (CPU, memory, timer, interrupts, joypad)

### Failing Tests
- Test 03: OP SP,HL (times out)
- Tests 04-11: Not yet attempted

### Known Issues
- Test 03 timeout - see development.md for investigation details
- Likely related to `ADD SP,e` or `LD HL,SP+e` flag calculations

---

## Debugging Workflow

1. **Unit test fails** → Check specific component test
2. **Blargg test fails** → Use diagnostic tools to trace execution
3. **Game doesn't work** → Use Tetris diagnostic tools
4. **Need to investigate** → Create focused test script, save in tests/

Example workflow for new bug:
```bash
# 1. Identify which component is failing
python tests/run_unit_tests.py all

# 2. Run Blargg tests to see error code
python tests/run_blargg_tests.py

# 3. Use diagnostic tools
python tests/diagnostic_tools.py trace_interrupts

# 4. Create focused test if needed
# ... write test_new_bug.py ...

# 5. Fix bug in src/

# 6. Verify fix
python tests/run_unit_tests.py all
python tests/run_blargg_tests.py
```

---

## Additional Resources

- `docs/development.md` - Current project status and known issues
- `docs/` - Implementation details for each component
