# Trace file

The emulator writes a trace file by default, to help see what a game does with the LCD, video memory and DMA.

```bash
python -m src.emulator game.gb             # writes tracing/tracing.txt
python -m src.emulator game.gb --no-trace  # no trace, slightly faster
```

The file lives in `tracing/` at the project root (ignored by git) and is overwritten on each run. Tracing wraps the memory bus's general read and write functions. Plain ROM and RAM accesses take a fast path that bypasses them, so the cost is small and limited to I/O and video-memory accesses.

## Entries

Each entry starts with the T-cycle count and, for accesses, the PC of the instruction.

| Entry | When it is logged | Example |
|---|---|---|
| LCD on/off | Every LCDC write that changes the value | `[    137780] PC=0x023D WRITE LCDC: 0x00 (LCD OFF)` |
| VRAM write | Non-zero writes: the first 100, then every 100th | `[    449388] PC=0x279E WRITE VRAM [0x9BFF] = 0x2F` |
| LY read | Every 1000th read of LY (0xFF44) | `[    522724] PC=0x282A READ LY: 60` |
| DMA start | Every write to 0xFF46 | `[    500000] PC=0x0280 DMA TRANSFER from 0xC000` |
| State | Once a second (60 frames) | `[   4000000] STATE: LY=47  LCDC=0xD3 (LCD ON) PC=0x02EF` |
| Sections | Start, ROM loaded, stop (with totals) | `EMULATOR STOPPED`, `Total VRAM writes: ...` |

The emulator also has a VBlank entry (`*** VBLANK INTERRUPT ***`). It is checked once per frame, after the frame has run, and by then the game's handler has normally cleared the flag. In practice it is rarely or never written.

## Reading a trace

```bash
grep "LCD OFF" tracing/tracing.txt        # when the game turns the screen off
grep "DMA" tracing/tracing.txt | head     # where sprite data is copied from
grep "STATE" tracing/tracing.txt          # one line per second
```

For instruction-level logs, use Gameboy Doctor mode instead (`GAMEBOY_DOCTOR=1`). It writes CPU state in the format of [Gameboy Doctor](https://github.com/robert/gameboy-doctor), which can be compared line by line with reference logs.
