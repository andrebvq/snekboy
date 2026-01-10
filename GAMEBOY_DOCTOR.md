# Gameboy Doctor Integration

This document explains how to use and remove the Gameboy Doctor integration for CPU trace debugging.

## Overview

Gameboy Doctor is a tool that compares your emulator's CPU execution log against reference logs to identify bugs. This integration adds logging capability to the emulator without affecting normal operation.

## How to Use

### Method 1: Using the Runner Script (Recommended)

```bash
python run_gameboy_doctor.py <rom_file> [max_cycles]
```

Examples:
```bash
# Run a Blargg test ROM
python run_gameboy_doctor.py tests/roms/03-op_sp_hl.gb

# Run for 2 million cycles
python run_gameboy_doctor.py tests/roms/01-special.gb 2000000
```

This will:
1. Enable Gameboy Doctor mode automatically
2. Initialize CPU to the correct test state
3. Run the ROM and generate `emulator_log.txt`
4. Show execution progress and serial output

### Method 2: Manual Activation

Set the environment variable before running your code:

**Windows (PowerShell):**
```powershell
$env:GAMEBOY_DOCTOR=1
python your_script.py
```

**Windows (CMD):**
```cmd
set GAMEBOY_DOCTOR=1
python your_script.py
```

**Linux/Mac:**
```bash
export GAMEBOY_DOCTOR=1
python your_script.py
```

### Method 3: In Python Code

```python
import os
os.environ['GAMEBOY_DOCTOR'] = '1'

from src.cpu import CPU
from src.gameboy_doctor import initialize_cpu_for_doctor

cpu = CPU()
cpu.memory.load_rom_file("test.gb")

# Initialize to Blargg test state
initialize_cpu_for_doctor(cpu)

# Run normally - logging happens automatically
while cpu.total_cycles < 1_000_000:
    cpu.step()
```

## What Gets Modified

When `GAMEBOY_DOCTOR=1` is set:

1. **CPU Logging**: Every instruction execution is logged to `emulator_log.txt`
2. **LY Register Override**: Reads from 0xFF44 (LY) return 0x90 (VBlank) to avoid timing issues
3. **Initial State**: Use `initialize_cpu_for_doctor(cpu)` to set registers to Blargg test entry point

When the environment variable is **not set** or is `0`:
- **Zero overhead**: No logging occurs
- **Normal behavior**: LY register works normally
- **No performance impact**: Logger is `None`

## Log Format

Each line in `emulator_log.txt` follows this exact format:
```
A:01 F:B0 B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0100 PCMEM:00,00,00,00
```

Where:
- `A`, `B`, `C`, `D`, `E`, `H`, `L`: 8-bit registers (2-digit hex)
- `F`: Flags register (Z=bit7, N=bit6, H=bit5, C=bit4)
- `SP`, `PC`: 16-bit registers (4-digit hex)
- `PCMEM`: Next 4 bytes at PC (comma-separated hex)

## Comparing with Reference Logs

After generating your log, use Gameboy Doctor to compare:

```bash
gameboy-doctor <rom_file> emulator_log.txt
```

This will show where your emulator diverges from the expected execution.

## Files Involved

The Gameboy Doctor integration consists of:

### New Files (can be deleted to remove feature)
- `src/gameboy_doctor.py` - All Gameboy Doctor logic
- `run_gameboy_doctor.py` - Runner script for tests
- `GAMEBOY_DOCTOR.md` - This documentation
- `test_doctor_integration.py` - Integration test

### Modified Files (minimal changes)
- `src/cpu.py` - 3 lines added:
  - Import statement
  - Logger initialization
  - Log call after each step
- `src/memory.py` - 2 lines added:
  - Import statement
  - LY register override

## How to Remove

To completely remove Gameboy Doctor support:

1. **Delete these files:**
   ```
   src/gameboy_doctor.py
   run_gameboy_doctor.py
   GAMEBOY_DOCTOR.md
   test_doctor_integration.py
   ```

2. **In `src/cpu.py`, remove these 3 lines:**
   ```python
   # Line ~13: Remove import
   from src.gameboy_doctor import create_logger_if_enabled

   # Line ~60: Remove logger creation
   self._doctor_logger = create_logger_if_enabled()

   # Lines ~511-512: Remove logging call
   if self._doctor_logger:
       self._doctor_logger.log_step(self)
   ```

3. **In `src/memory.py`, remove these 4 lines:**
   ```python
   # Line ~21: Remove import
   from src.gameboy_doctor import should_override_ly_register, get_overridden_ly_value

   # Lines ~84-85: Remove LY override
   if address == 0xFF44 and should_override_ly_register():
       return get_overridden_ly_value()
   ```

That's it! The emulator will work exactly as before with no trace of the integration.

## Performance Impact

- **When disabled (default)**: Zero overhead - logger is `None`, checks are fast
- **When enabled**: ~10-20% slowdown due to file I/O for each instruction

For normal emulation, always keep `GAMEBOY_DOCTOR` unset or set to `0`.

## Troubleshooting

**Log file not created:**
- Check write permissions in the current directory
- Check that `GAMEBOY_DOCTOR=1` is set

**Log format doesn't match:**
- Verify you're using the exact format from this integration
- Check that F register bits are correct (Z=7, N=6, H=5, C=4)

**Emulator crashes with Gameboy Doctor enabled:**
- This is likely a bug in the emulator itself
- The crash location in the log can help identify the problem

**LY register always returns 0x90:**
- This is intentional when Gameboy Doctor mode is enabled
- Disable Gameboy Doctor mode for normal LY behavior

## Example: Running Blargg Tests

```bash
# Download Blargg test ROMs
# Place them in tests/roms/

# Run test with Gameboy Doctor
python run_gameboy_doctor.py tests/roms/cpu_instrs/individual/03-op_sp_hl.gb 10000000

# Check the serial output for "Passed" or "Failed"
# Compare log with reference
gameboy-doctor tests/roms/cpu_instrs/individual/03-op_sp_hl.gb emulator_log.txt
```
