# Gameboy Doctor PC Logging Fix

## Issue Reported

From Gameboy Doctor output:
```
MINE:   A:01 F:CH-Z B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0100
YOURS:  A:01 F:CH-Z B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0101
```

**Problem**: PC was off by 1 (logging 0x0101 instead of 0x0100)

## Root Cause

The logger was recording PC **after** the fetch operation instead of **before**.

### What Gameboy Doctor Expects

For each instruction log entry:
- **PC**: Where the instruction **was located** (before fetch)
- **Registers**: State **after execution**
- **PCMEM**: Bytes at the **current PC** (after execution)

Example timeline for a NOP at 0x0100:
1. PC = 0x0100 (before fetch) ← **This goes in the log**
2. Fetch opcode (PC becomes 0x0101)
3. Execute NOP
4. Registers updated (none for NOP)
5. Log: `PC:0100` (before) with `PCMEM` from current PC (0x0101)

## The Fix

### Changed Files

**1. `src/cpu.py`** (2 changes):

Added line to capture PC before fetch:
```python
# Gameboy Doctor: Capture PC before fetch for logging
pc_before_fetch = self.registers._pc if self._doctor_logger else None

# FETCH
opcode = self.fetch_byte()
```

Updated logging call to pass the captured PC:
```python
# Gameboy Doctor: Log with PC from before fetch, but current register state
if self._doctor_logger:
    self._doctor_logger.log_step(self, pc_before_fetch)
```

**2. `src/gameboy_doctor.py`** (1 change):

Updated `log_step()` signature and implementation:
```python
def log_step(self, cpu, pc_before_fetch):
    """
    Log CPU state in Gameboy Doctor format

    The PC in the log represents where the instruction WAS (before fetch),
    while registers show their state AFTER execution, and PCMEM shows
    the bytes at the current PC (after execution).

    Args:
        cpu: CPU instance with registers and memory
        pc_before_fetch: PC value before the instruction was fetched
    """
    # ... get current register state ...
    pc_current = cpu.registers._pc  # Current PC (after execution)

    # Get PCMEM from current PC
    pc_mem = []
    for i in range(4):
        addr = (pc_current + i) & 0xFFFF
        pc_mem.append(cpu.memory.read_byte(addr))

    # Format log with PC from BEFORE fetch
    log_line = (
        f"A:{a:02X} F:{f:02X} B:{b:02X} C:{c:02X} "
        f"D:{d:02X} E:{e:02X} H:{h:02X} L:{l:02X} "
        f"SP:{sp:04X} PC:{pc_before_fetch:04X} PCMEM:{pc_mem_str}\n"
    )
```

## Verification

### Before Fix
```
A:01 F:B0 B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0101 PCMEM:00,00,00,00
                                                    ^^^^
                                                    WRONG (after fetch)
```

### After Fix
```
A:01 F:B0 B:00 C:13 D:00 E:D8 H:01 L:4D SP:FFFE PC:0100 PCMEM:00,00,00,00
                                                    ^^^^
                                                    CORRECT (before fetch)
```

### Test Results

All verification tests pass:
```
✅ PASS: Normal Mode
✅ PASS: Doctor Mode
✅ PASS: Log Format
✅ PASS: LY Override
✅ PASS: CPU Initialization
TOTAL: 5/5 tests passed
```

## Impact

- **Performance**: Minimal - one extra variable assignment when Doctor mode enabled
- **Normal mode**: Zero impact - conditional only evaluates when `_doctor_logger` is not None
- **Log format**: Now matches Gameboy Doctor expectations exactly

## Testing

Run the verification suite:
```bash
python verify_gameboy_doctor.py
```

Or test specifically:
```bash
python test_pc_fix.py
```

Expected output:
```
PC in log: 0x0100
✅ CORRECT: PC logged as 0x0100 (before fetch)
```

## Next Steps

With this fix, your logs should now match Gameboy Doctor's reference logs for the PC value. Continue debugging by:

1. Running test ROMs with the fixed logger
2. Comparing logs with Gameboy Doctor
3. Fixing any remaining instruction implementation bugs

---

**Fix Status**: ✅ Complete and Verified
**Tests Passing**: 5/5
**Ready for**: Gameboy Doctor comparison
