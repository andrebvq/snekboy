# Complete Debugging Session History

This document contains all debugging sessions, investigations, and fixes applied to the SnekBoy emulator.

---

## Table of Contents
1. [Resolved & Working](#resolved--working)
2. [Investigated But Not Yet Working](#investigated-but-not-yet-working)
3. [Debugging Techniques Used](#debugging-techniques-used)

---

# Resolved & Working

## Session 1: Blargg Test 01 - Arithmetic & Flags

### Bug 1.1: ADD Instruction Type Mismatch
**Symptom:** Garbled serial output like `0[F7]:0[FB]` instead of readable test results.

**Investigation:**
- Test 01 was failing with unreadable characters
- Traced execution and found immediate ADD operations weren't working
- Discovered type mismatch: decoder returns string `'IMMEDIATE'`, but code checked for enum `ArithmeticTarget.IMMEDIATE`

**Root Cause:** String vs enum comparison always failed, breaking all immediate arithmetic.

**Fix:** Modified `_execute_add()` to use `_get_operand_value()` helper which handles both types.

**File:** `src/cpu.py` - `_execute_add()` method

**Result:** Test output became readable: `01:02  02:02  03`

---

### Bug 1.2: POP AF Register Masking
**Symptom:** Test 01 showing error code 05 instead of "ok"

**Investigation:**
- Test was failing on flag register operations
- Game Boy hardware requirement: F register lower 4 bits (3-0) must always be 0
- POP AF was loading all 8 bits from stack without masking

**Root Cause:** Missing bit mask when loading values into F register.

**Fix:** Applied 0xF0 mask when loading F register in `Flags.from_byte()`:
```python
self._bits = BitField(validate_byte(value) & 0xF0)
```

**File:** `src/registers.py` - `Flags.from_byte()` method

**Result:** Test 01 passes completely: `01:ok`

---

## Session 2: Blargg Test 02 - Timer & Interrupts

### Bug 2.1: T-cycles vs M-cycles Confusion (CRITICAL)
**Symptom:** Test 02 failing at sub-test 04 with output `02:04` ("Timer doesn't work")

**Investigation:**
- Test 02 sub-test 04 uses precise delay loop timing
- Timer was running 4x too fast
- Found Reddit thread with EXACT same issue: developer forgot to convert T-cycles to M-cycles
- Discovered all instruction timings are in T-cycles, but timer expects M-cycles

**Root Cause:**
- Opcode table stores cycle counts in T-cycles
- `_update_timers()` expects M-cycles
- 1 M-cycle = 4 T-cycles
- Timer was being updated with T-cycles as if they were M-cycles

**Fix:** Convert T-cycles to M-cycles before updating timers:
```python
m_cycles = cycles // 4
self._update_timers(m_cycles)
```

Applied in 3 locations:
1. Normal instruction execution
2. HALT state
3. Interrupt handling

**File:** `src/cpu.py` - `step()` method (lines 452-453, 416-418, 431-433)

**Result:** Timer now runs at correct speed, test 02 progresses further

**Reference:** [Reddit: Unable to pass Blargg's 02-interrupts test](https://www.reddit.com/r/EmuDev/comments/1djjcz7/gameboy_unable_to_pass_blarggs_02interrupts_test/)

---

### Bug 2.2: run_until() Stopping on HALT
**Symptom:** Test 02 showing just `02` with no result, halting at 12.6M cycles

**Investigation:**
- Test ROM uses HALT to wait for timer interrupts
- `run_until()` had condition `and not self.halted` that stopped execution
- Timers must keep running during HALT
- Interrupts must be able to wake CPU from HALT

**Root Cause:** Stopping execution completely when HALT executed prevented:
1. Timers from continuing to run
2. Interrupts from being generated
3. CPU from waking up

**Fix:** Removed halt check from `run_until()`:
```python
# Continue stepping even when halted - timers need to run
while self.total_cycles < target_cycles:
    self.step()
```

**File:** `src/cpu.py` - `run_until()` method

**Result:** Test 02 completes: `02:ok`

---

### Bug 2.3: Interrupt Service Missing Wake/Cancel Logic
**Symptom:** CPU might not properly exit HALT when interrupt serviced

**Investigation:**
- When servicing interrupt, CPU must: exit HALT, cancel pending EI, disable IME, jump to vector
- Original code missing wake and cancel logic

**Fix:** Added to `_service_interrupt()`:
```python
self._ei_pending = False  # Cancel pending EI
self.halted = False       # Exit HALT mode
```

**File:** `src/cpu.py` - `_service_interrupt()` method

**Result:** Proper interrupt handling during HALT

---

## Session 3: Joypad Implementation

### Feature: Complete Joypad System
**Requirement:** Implement Game Boy joypad with specific key mappings

**Implementation:**
1. **P1 Register (0xFF00) Handling**
   - Bit 5: Select button keys (0=select)
   - Bit 4: Select direction keys (0=select)
   - Bits 3-0: Button states (0=pressed, 1=not pressed)
   - Inverted logic throughout

2. **Joypad Class** (`src/joypad.py`)
   - Button state tracking for all 8 buttons
   - `read_p1()` returns correct value based on selected group
   - `write_p1()` handles group selection
   - Interrupt triggering on button press

3. **Memory Integration** (`src/memory.py`)
   - P1 register at 0xFF00 connected to joypad
   - Read/write handlers for joypad access

4. **Display Input** (`src/display.py`)
   - KEYDOWN/KEYUP event handling
   - Key mappings: A='A', B='S', Start='Z', Select='X', D-Pad='I/K/J/L'

5. **Emulator Connection** (`src/emulator.py`)
   - Joypad passed to display event handler
   - Control instructions printed on startup

**Result:** Full joypad system working, all unit tests pass

---

## Session 4: Tetris Game Interrupt Debugging

### Bug 4.1: EI (Enable Interrupts) Instruction Delay
**Symptom:** Tetris stuck in polling loop, interrupts firing at wrong time

**Investigation:**
1. Traced IME state changes during Tetris execution
2. Found EI at 0x02BA should enable interrupts
3. Discovered interrupt fired IMMEDIATELY after EI instead of after delay
4. Game Boy hardware: EI enables interrupts AFTER next instruction executes (1-instruction delay)

**Detailed Trace:**
```
[495,128] PC=0x02BA: EI    - IME: False -> True   <- Should stay False!
[495,148] PC=0x02BB: [0xAF] - IME: True -> False  <- Interrupt fired too early
```

**Root Cause:**
- EI set `_ei_pending = True`
- IME was set to True at end of same instruction
- Next `step()` checked interrupts at start with IME=True
- Interrupt fired before delay instruction completed

**Fix:** Changed `_ei_pending` from boolean to integer counter:
```python
# In _execute_ei():
self._ei_pending = 2  # Set counter to 2

# In step():
if self._ei_pending > 0:
    self._ei_pending -= 1
    if self._ei_pending == 0:
        self.ime = True
```

This ensures: 2 (EI executes) → 1 (delay instruction executes) → 0 (IME enabled)

**File:** `src/instructions_impl.py:543` and `src/cpu.py` step() method

**Result:** EI now implements correct 1-instruction delay, interrupts fire at right time

---

### Bug 4.2: RETI Not Enabling Interrupts
**Symptom:** After first VBlank interrupt, game stuck in loop with IME=False

**Investigation:**
1. Traced execution through VBlank ISR
2. ISR used RET instead of RETI initially, but found RETI at 0x020B later
3. After RETI executed, IME stayed False
4. Checked RETI implementation - found TODO comment with `pass` statement

**Root Cause:** RETI instruction was never implemented, just had placeholder:
```python
def _execute_reti(self) -> None:
    # ... pop PC from stack ...
    # Enable interrupts (TODO: implement IME flag)
    pass  # BUG: Does nothing!
```

**Fix:** Implemented RETI properly:
```python
def _execute_reti(self) -> None:
    # ... pop PC from stack ...
    self.ime = True           # Enable interrupts immediately
    self._ei_pending = 0      # Cancel any pending EI
```

**File:** `src/instructions_impl.py:525-528`

**Result:** RETI now re-enables interrupts, game can continue receiving VBlank interrupts

---

### Verification: Both Fixes Working
**Test:** Created comprehensive test suite for interrupt instructions

**Tests:**
1. EI delay - verifies `_ei_pending` counter works correctly
2. RETI enables interrupts - verifies IME set to True
3. Interrupt fires after EI delay - verifies timing is correct

**All tests PASS**

**Impact on Tetris:**
- Game progresses past initial polling loop
- VBlank interrupts fire correctly
- Interrupt handlers execute and return properly
- Game continues initialization (memory clearing, etc.)

---

## Session 5: Timer Enhancements

### Enhancement: TIMA Write During Overflow
**What:** Implemented obscure Game Boy behavior for TIMA register

**Behavior:** Writing to TIMA during the 4-cycle overflow delay cancels the reload from TMA and the interrupt request.

**Implementation:** Track overflow state and cancel on write

**File:** `src/memory.py` - `write_byte()` for address 0xFF05

---

### Enhancement: TAC Write Obscure Behavior
**What:** Falling-edge detection when TAC register modified

**Behavior:** When TAC register is written, if the AND gate output (bit selected by frequency & timer enabled) transitions from 1→0, it triggers a spurious timer tick.

**Implementation:** Track previous AND gate state, detect falling edge

**File:** `src/memory.py` - `write_byte()` for address 0xFF07

---

# Investigated But Not Yet Working

## Issue 1: Blargg Test 03 Timeout

### Symptom
Test 03 (op sp,hl) doesn't complete within 30M cycles, just shows `03` with no result.

### Investigation Performed

#### 1. Execution Tracing
- Traced instruction execution through test initialization
- Verified test ROM loads and starts executing
- No obvious crashes or infinite loops detected
- Test appears to be running but very slowly

#### 2. Instruction Candidates
Test 03 focuses on SP and HL operations:
- `ADD SP,e` - Add signed immediate to SP
- `LD HL,SP+e` - Load SP+signed offset into HL
- `LD SP,HL` - Load HL into SP
- Stack operations with HL

#### 3. Flag Verification Attempts
Created multiple test cases for:
- `ADD SP,e` flag calculations (H and C flags)
- Half-carry detection for 16-bit adds
- Signed offset handling

**Findings:**
- Basic flag tests pass
- Half-carry logic appears correct for normal cases
- May be edge case with specific values

#### 4. Timing Investigation
- Verified instruction cycle counts match opcode table
- Checked if test has unreasonable cycle requirements
- Test 02 completes in ~13M cycles, test 03 timeout at 30M seems unusual

### Current Status
**UNRESOLVED** - Test 03 still times out

### Potential Root Causes
1. **Flag calculation bug** in `ADD SP,e` or `LD HL,SP+e`
   - Half-carry (H flag) calculation may have edge case
   - Carry (C flag) calculation for signed arithmetic
2. **Instruction implementation error** causing incorrect behavior
3. **Timing issue** - instructions take wrong number of cycles
4. **Unknown edge case** in SP/HL operations

### Documentation
See `docs/test_03_investigation_summary.md` for detailed investigation notes.

### Next Steps for Future Developer
1. Create minimal test case for `ADD SP,e` with all edge cases
2. Compare flag outputs with reference emulator (BGB, SameBoy)
3. Trace test 03 execution in reference emulator side-by-side
4. Focus on half-carry calculation for 16-bit signed adds
5. Check if test has specific timing requirements

---

## Issue 2: Tetris Gameplay Not Tested

### Status
Tetris ROM loads, displays copyright screen, and progresses through initialization.

### Not Yet Verified
- Full game progression to title screen
- Menu navigation with joypad
- Gameplay mechanics
- Scoring, level progression
- Game over handling

### Why Not Tested
Blocked on Blargg test 03 - want to ensure core CPU is fully correct before testing complex game logic.

### Next Steps
1. Resolve test 03 first
2. Run Tetris to title screen
3. Test joypad input in menus
4. Verify gameplay works correctly

---

# Debugging Techniques Used

## 1. Execution Tracing
Created trace scripts that log every instruction executed with register state:
```python
print(f"[{cycle}] PC=0x{pc:04X}: {instruction} A={a:02X} Flags={flags}")
```

**Used For:**
- Finding where execution gets stuck
- Verifying instruction sequences
- Tracking register value changes

## 2. Targeted Value Monitoring
Watch specific memory locations for changes:
```python
if new_value != last_value:
    print(f"[{cycle}] 0xFF85 changed: {last_value:02X} -> {new_value:02X}")
```

**Used For:**
- Tracking game state variables
- Monitoring I/O register changes
- Detecting when values update

## 3. Interrupt Flow Tracing
Log interrupt enable/disable and firing:
```python
if ime_before != ime_after:
    print(f"IME changed: {ime_before} -> {ime_after}")
```

**Used For:**
- Debugging EI/DI/RETI timing
- Verifying interrupt handlers execute
- Finding interrupt-related bugs

## 4. Comparison Testing
Run same code in reference emulator and compare:
- Register states
- Memory contents
- Timing

**Used For:**
- Validating instruction implementations
- Finding subtle differences
- Confirming bug fixes

## 5. Unit Testing
Created isolated tests for specific features:
- Individual instructions
- Flag calculations
- Timer behavior
- Interrupt timing

**Used For:**
- Regression testing
- Verifying fixes don't break other things
- Documenting expected behavior

## 6. Serial Output Analysis
Capture and analyze serial port output from test ROMs:
```
cpu_instrs

01:ok  02:ok  03
```

**Used For:**
- Determining which test failed
- Getting error codes from tests
- Confirming test completion

## 7. Cycle Counting
Track exact cycle counts for events:
```python
print(f"Event occurred at cycle {cpu.total_cycles}")
```

**Used For:**
- Timing-sensitive bugs
- Comparing to expected timing
- Finding timing-related issues

## 8. State Snapshots
Capture complete CPU/memory state at specific points:
```python
snapshot = {
    'pc': cpu.registers._pc,
    'sp': cpu.registers._sp,
    'ime': cpu.ime,
    'memory': cpu.memory._data[0xFF00:0xFF80].copy()
}
```

**Used For:**
- Before/after comparisons
- Finding state corruption
- Debugging complex bugs

---

# Key Lessons Learned

## 1. T-cycles vs M-cycles
**Lesson:** Always verify which timing unit code expects. 1 M-cycle = 4 T-cycles.

**Impact:** This was the single most impactful bug fix, affecting all timing-related behavior.

## 2. Type System Matters
**Lesson:** Python's dynamic typing can hide bugs. String vs enum comparison fails silently.

**Solution:** Use type hints and helper functions that handle multiple types.

## 3. HALT is Not Stop
**Lesson:** HALT is a low-power state, not a complete stop. Timers must keep running.

**Impact:** Critical for interrupt-based game loops and test ROMs.

## 4. Hardware Quirks Are Real
**Lesson:** Game Boy has many obscure behaviors that matter:
- F register lower 4 bits always 0
- EI instruction 1-instruction delay
- Timer edge cases on register writes
- TIMA overflow delay

**Solution:** Read Pan Docs carefully, implement all edge cases.

## 5. Community Resources Are Invaluable
**Lesson:** Someone has likely had the same problem before.

**Resources:**
- Reddit r/EmuDev
- Discord servers
- Pan Docs
- GBEDG documentation

## 6. Test ROMs Are Essential
**Lesson:** Blargg test ROMs catch bugs that manual testing misses.

**Result:** Fixed 5+ bugs that weren't apparent from just running games.

## 7. Trace Everything
**Lesson:** When stuck, create a trace script. Print PC, registers, flags, memory.

**Benefit:** Visual inspection often reveals the bug immediately.

## 8. Start Simple
**Lesson:** Fix simple bugs first (arithmetic, flags) before complex ones (timers, interrupts).

**Reason:** Complex bugs often depend on simple functionality working correctly.

---

# References

## Documentation
- [Pan Docs](https://gbdev.io/pandocs/) - Complete GB technical reference
- [GBEDG](https://github.com/Hacktix/GBEDG) - Accurate timing documentation
- [Game Boy Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)

## Test ROMs
- [Blargg's Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite)

## Community
- [r/EmuDev](https://www.reddit.com/r/EmuDev/)
- [Critical Reddit Thread](https://www.reddit.com/r/EmuDev/comments/1djjcz7/gameboy_unable_to_pass_blarggs_02interrupts_test/)

## Reference Emulators
- BGB - Windows debugger
- SameBoy - Accurate emulator
- Gambatte - Cycle-accurate
