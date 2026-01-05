# Blargg Test Output Analysis

## Current Output

```
cpu_instrs

0[F7]:0[FB]  0[F8]:0[F8]  0[F9]
```

## What This Means

### Serial Port Working ✅
- We're successfully capturing serial output from 0xFF01/0xFF02
- Characters are being transmitted correctly
- Newlines are rendering properly

### Test Execution
The output format should be:
```
cpu_instrs

01:ok  02:ok  03:ok  04:ok  05:ok  06:ok  07:ok  08:ok  09:ok  10:ok  11:ok

Passed
```

But we're getting non-printable bytes (0xF7-0xF9) instead of ASCII digits.

## Analysis

### What the Codes Mean

According to Blargg test documentation:
- Tests print their number, then "ok" or a failure code
- The format is compact to avoid scrolling

Our output shows:
- "0" - ASCII digit (correct)
- [F7] - Non-printable byte (0xF7)
- ":" - ASCII colon (correct)
- "0" - ASCII digit (correct)
- [FB] - Non-printable byte (0xFB)

### Two Possible Interpretations

#### Theory 1: Tile/Graphics Data
The test ROMs write to both serial port AND screen tiles. The non-printable bytes 0xF7-0xFB might be tile indices for the graphical display. Since we don't have PPU implemented, these would appear as garbage in serial output.

**Problem**: But if this were tile data, why is it mixed with ASCII?

#### Theory 2: Character Encoding Issue
The values 0xF7-0xFB are being sent through serial, suggesting the ROM is trying to output something specific. These might be:
- Extended ASCII characters
- Special test framework codes
- Corrupted output due to instruction bugs

**More likely**: The test is trying to print digits "1", "2", "3", etc. but our CPU is producing wrong values.

### Expected vs Actual

**Expected**: "01:ok  02:ok  03:ok..."
**Actual**: "0[F7]:0[FB]  0[F8]:0[F8]  0[F9]"

The pattern suggests:
- First "0" is correct
- Second char should be "1" (0x31) but we get 0xF7
- Pattern continues with incrementing values

### The Smoking Gun

Looking at 0xF7, 0xF8, 0xF9:
- These ARE incrementing by 1
- They're way off from ASCII "1", "2", "3" (0x31, 0x32, 0x33)
- Difference: 0xF7 - 0x31 = 0xC6 (198 decimal)

## Likely Root Cause

The test is computing test numbers (1, 2, 3...) but the result is wrong by 0xC6.

Possible causes:
1. **DAA instruction bug** - Decimal Adjust Accumulator is complex and often buggy
2. **Flag handling error** - Wrong flags causing incorrect branches
3. **Arithmetic bug** - ADD/SUB/INC producing wrong results
4. **Memory corruption** - Values being corrupted in RAM

## How to Debug

### Step 1: Verify Basic Arithmetic
Test that:
- 0 + 1 = 1 (not 0xF7)
- Basic INC works correctly
- Character encoding is correct

### Step 2: Test Individual Instructions
Focus on:
- DAA (Decimal Adjust)
- ADD with carry flags
- INC with half-carry
- CP (compare) flag behavior

### Step 3: Run Individual Test ROMs
The readme mentions individual test ROMs in `individual/` directory. These would help isolate which instruction group is failing.

### Step 4: Use Gameboy Doctor
Consider using [gameboy-doctor](https://github.com/robert/gameboy-doctor) which logs every instruction execution and compares with known-good emulator.

## Next Actions

1. **Test basic arithmetic manually**
   ```python
   cpu = CPU()
   cpu.registers._a = 0
   cpu._execute_add('A', 1)  # Should give A=1, not A=0xF7
   ```

2. **Check DAA implementation**
   - DAA is notoriously tricky
   - Check against Pan Docs specification
   - Verify BCD arithmetic behavior

3. **Review flag behavior**
   - Half-carry calculation
   - Carry flag
   - Zero flag
   - Subtract flag (especially in DAA)

4. **Add debug logging**
   - Log register state before/after each instruction
   - Compare with known-good emulator traces

## References

- [Blargg cpu_instrs readme](https://github.com/loociano/ESboy/blob/master/roms/blargg/cpu_instrs/readme.txt)
- [Requirements for running blargg's tests](https://forums.nesdev.org/viewtopic.php?t=16174)
- [Gameboy emulator debugging parable](https://www.bkase.io/posts/gameboy-debugging-parable)
- [Gameboy Doctor tool](https://github.com/robert/gameboy-doctor)
- [Testing with Blargg ROMs](https://emudev.de/gameboy-emulator/testing-our-cpu/)

## Conclusion

The test IS running and producing output, but the values are wrong. This points to a CPU instruction implementation bug rather than missing opcodes. The systematic offset (0xC6) in the values suggests a specific arithmetic or encoding issue that affects how test numbers are calculated or displayed.

**Priority**: Debug arithmetic and flag behavior, especially DAA instruction.
