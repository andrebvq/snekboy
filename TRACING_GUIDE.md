# Execution Tracing Guide

## Overview

The emulator now includes built-in execution tracing that logs critical events to `tracing.txt` in real-time.

## How to Use

### Basic Usage (Tracing Enabled by Default)

```bash
# Run emulator with tracing enabled (default)
python -m src.emulator "path/to/rom.gb"
```

This will:
- Start the emulator normally
- Create/overwrite `tracing.txt` with execution logs
- Log events as they happen in real-time
- Close the trace file when you quit the emulator (ESC key)

### Disable Tracing

```bash
# Run without tracing (for better performance)
python -m src.emulator "path/to/rom.gb" --no-trace
```

## What Gets Logged

The tracer logs these key events:

### 1. LCDC Writes (LCD ON/OFF transitions)
```
[   137780] PC=0x023D WRITE LCDC: 0x00 (LCD OFF)
[   494896] PC=0x038A WRITE LCDC: 0xD3 (LCD ON)
```

**When to check:** If game gets stuck with black screen or frozen display

### 2. VRAM Writes
```
[   449388] PC=0x279E WRITE VRAM [0x9BFF] = 0x2F
[   449432] PC=0x279E WRITE VRAM [0x9BFE] = 0x2F
```

**Sampling:** First 100 writes logged in full, then every 100th write

**When to check:** To verify game is updating graphics

### 3. LY Register Reads
```
[  1000000] PC=0x02ED READ LY: 144
[  2000000] PC=0x02ED READ LY: 89
```

**Sampling:** Every 1000th read to avoid spam

**When to check:** To see if game is polling for VBlank

### 4. DMA Transfers
```
[   500000] PC=0x0280 DMA TRANSFER from 0xC000
```

**When to check:** To verify sprite data is being copied to OAM

### 5. VBlank Interrupts
```
[  1007320] *** VBLANK INTERRUPT ***
```

**Frequency:** Logged once per second (every 60th VBlank)

**When to check:** To verify interrupts are firing

### 6. State Snapshots
```
[  4000000] STATE: LY=47  LCDC=0xD3 (LCD ON) PC=0x02EF
```

**Frequency:** Once per second

**When to check:** Quick overview of emulator state

## Understanding the Logs

### Example: Stage Selection Freeze

When Tetris gets stuck at stage selection, the log might show:

```
[25000000] STATE: LY=3   LCDC=0x53 (LCD ON)  PC=0x02ED
[25000000] *** START BUTTON PRESSED ***
[25500000] PC=0x2834 WRITE LCDC: 0x00 (LCD OFF)
[26000000] STATE: LY=91  LCDC=0x00 (LCD OFF) PC=0x02ED
[27000000] STATE: LY=133 LCDC=0x00 (LCD OFF) PC=0x02ED
[28000000] STATE: LY=21  LCDC=0x00 (LCD OFF) PC=0x02ED
```

**Diagnosis:**
- LCD turns OFF at cycle 25,500,000
- LY continues advancing (91, 133, 21...) - this is correct
- LCD never turns back ON
- PC stuck at 0x02ED (VBlank wait loop)

**Problem:** Game is stuck waiting for some condition while LCD is OFF

### What to Look For

1. **LCD stays OFF too long:**
   - Check if VRAM writes happen during LCD OFF period
   - If no VRAM writes, game might be stuck in a loop

2. **VRAM writes stop:**
   - Count VRAM writes before and after key events
   - If writes stop after pressing a button, input handling failed

3. **LY doesn't advance:**
   - Should see LY cycling through 0-153
   - If stuck at one value, timing bug

4. **No DMA transfers:**
   - Tetris should use DMA to copy sprites
   - If no DMA after boot, sprites won't appear

## Performance Impact

Tracing has minimal performance impact:
- LY reads: Only 1 in 1000 logged
- VRAM writes: Only 1 in 100 logged (after first 100)
- LCDC writes: All logged (infrequent)
- DMA: All logged (infrequent)

**Typical file size:** 1-5 MB for several minutes of gameplay

## Tips

### Finding Specific Events

Use grep or text editor search to find specific events:

```bash
# Find all LCD OFF events
grep "LCD OFF" tracing.txt

# Find all VRAM writes after cycle 25M
grep "WRITE VRAM" tracing.txt | grep "^\[2[5-9]"

# Find state at specific cycle range
grep "STATE" tracing.txt | grep "^\[30"
```

### Comparing Runs

Run the emulator twice and compare traces:

```bash
# First run
python -m src.emulator tetris.gb
# Play to stage select, press START, quit
mv tracing.txt trace1.txt

# Second run
python -m src.emulator tetris.gb
# Try different input timing
mv tracing.txt trace2.txt

# Compare
diff trace1.txt trace2.txt
```

### Debugging Specific Issues

**Issue: Game frozen after pressing button**
1. Find the button press time in console output
2. Search trace for LCDC changes near that cycle count
3. Check if VRAM writes stop
4. Look for unusual PC values

**Issue: Black screen**
1. Check LCDC value - should have bit 7 set (0x80+)
2. Check if any VRAM writes happened
3. Verify VBlank interrupts are firing

**Issue: Sprites not appearing**
1. Search for "DMA TRANSFER"
2. Should see transfers every frame
3. Check source address is reasonable (0xC000-0xDF00 typically)

## Trace File Structure

```
================================================================================
EMULATOR EXECUTION TRACE
================================================================================

================================================================================
ROM LOADED AND BOOT ROM SIMULATED
================================================================================

[         0] STATE: LY=0   LCDC=0x91 (LCD ON) PC=0x0100

================================================================================
EMULATOR STARTED
================================================================================

[    100000] PC=0x0233 WRITE LCDC: 0x80 (LCD ON)
[    137768] PC=0x023D WRITE LCDC: 0x03 (LCD OFF)
...

[  1007320] *** VBLANK INTERRUPT ***
[  4000000] STATE: LY=47  LCDC=0xD3 (LCD ON) PC=0x02EF

================================================================================
EMULATOR STOPPED
================================================================================
Total cycles: 30,000,000
Total VRAM writes: 5009
Total LY reads: 50000
```

## Troubleshooting

**Trace file not created:**
- Check file permissions in the project directory
- Make sure you're running from the correct directory

**Trace file huge (>100MB):**
- Normal for long sessions
- Use `--no-trace` flag for better performance
- Restart emulator to reset file

**Can't find event in trace:**
- Event might not be logged (check sampling rates above)
- Try searching for nearby cycle counts
- Check section headers (================)
