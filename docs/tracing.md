# Execution Tracing

Built-in execution tracing system for debugging and analysis.

## Usage

### Basic Usage (Tracing Enabled by Default)

```bash
python -m src.emulator "path/to/rom.gb"
```

Creates/overwrites `tracing.txt` with execution logs.

### Disable Tracing

```bash
python -m src.emulator "path/to/rom.gb" --no-trace
```

## Logged Events

### LCDC Writes
LCD ON/OFF transitions:
```
[   137780] PC=0x023D WRITE LCDC: 0x00 (LCD OFF)
[   494896] PC=0x038A WRITE LCDC: 0xD3 (LCD ON)
```

### VRAM Writes
```
[   449388] PC=0x279E WRITE VRAM [0x9BFF] = 0x2F
[   449432] PC=0x279E WRITE VRAM [0x9BFE] = 0x2F
```

Sampling: First 100 writes logged in full, then every 100th write.

### LY Register Reads
```
[  1000000] PC=0x02ED READ LY: 144
[  2000000] PC=0x02ED READ LY: 89
```

Sampling: Every 1000th read.

### DMA Transfers
```
[   500000] PC=0x0280 DMA TRANSFER from 0xC000
```

### VBlank Interrupts
```
[  1007320] *** VBLANK INTERRUPT ***
```

Frequency: Logged once per second (every 60th VBlank).

### State Snapshots
```
[  4000000] STATE: LY=47  LCDC=0xD3 (LCD ON) PC=0x02EF
```

Frequency: Once per second.

## Analyzing Logs

### Finding Specific Events

Use grep or text editor search:

```bash
# Find all LCD OFF events
grep "LCD OFF" tracing.txt

# Find all VRAM writes after cycle 25M
grep "WRITE VRAM" tracing.txt | grep "^\[2[5-9]"

# Find state at specific cycle range
grep "STATE" tracing.txt | grep "^\[30"
```

### Comparing Runs

```bash
# First run
python -m src.emulator tetris.gb
mv tracing.txt trace1.txt

# Second run
python -m src.emulator tetris.gb
mv tracing.txt trace2.txt

# Compare
diff trace1.txt trace2.txt
```

## Diagnostic Patterns

### Game Frozen After Button Press
1. Find the button press time in console output
2. Search trace for LCDC changes near that cycle count
3. Check if VRAM writes stop
4. Look for unusual PC values

### Black Screen
1. Check LCDC value - should have bit 7 set (0x80+)
2. Check if any VRAM writes happened
3. Verify VBlank interrupts are firing

### Sprites Not Appearing
1. Search for "DMA TRANSFER"
2. Transfers should occur every frame
3. Check source address is reasonable (0xC000-0xDF00 typically)

## Performance Impact

Tracing has minimal performance impact:
- LY reads: Only 1 in 1000 logged
- VRAM writes: Only 1 in 100 logged (after first 100)
- LCDC writes: All logged (infrequent)
- DMA: All logged (infrequent)

Typical file size: 1-5 MB for several minutes of execution.

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
- Verify running from the correct directory

**Trace file large (>100MB):**
- Normal for long sessions
- Use `--no-trace` flag for better performance
- Restart emulator to reset file

**Event not found in trace:**
- Event might not be logged (check sampling rates)
- Try searching for nearby cycle counts
- Check section headers (================)
