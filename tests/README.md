# Tests

## Running

```bash
pip install pytest
python -m pytest tests                 # all 75 unit tests, about a minute
python -m pytest tests/test_ppu.py -q  # one file
python tests/run_all_test_roms.py      # Blargg ROMs from test_roms/
```

`test_display.py` uses SDL's dummy video driver, so no window opens.

## Unit tests

| File | Tests | Covers |
|---|---|---|
| `test_cpu.py` | 8 | Instruction behaviour; the dispatch table against the decoder for every opcode and CB opcode |
| `test_fast_ops.py` | 2 | Each dedicated handler against the generic one, 40 random states per opcode (registers, flags, memory, bus timing, cycles) |
| `test_interrupts.py` | 11 | EI/DI delay, dispatch and IE push, HALT bug, DIV-write edge, TIMA reload cycle; timer fast path against the exact path |
| `test_timer.py` | 4 | DIV and TIMA rates, TMA reload |
| `test_timing.py` | 7 | Per-access timing, OAM DMA window and restart, serial transfer, joypad interrupt |
| `test_halt_skip.py` | 1 | HALT skip-ahead against one-M-cycle idling, 60 random timer/PPU setups |
| `test_lazy_sync.py` | 3 | The frame loop against plain `step()` on random I/O programs: registers before every instruction, the timing of every I/O access, final timer/PPU state and screen |
| `test_ppu.py` | 17 | Tile addressing, window, sprite priority, LCD off/on, STAT line, mode-3 length, line 153 |
| `test_memory.py` | 4 | Basic reads and writes |
| `test_memory_map.py` | 6 | Read-only ROM, echo RAM, unusable area, unused I/O bits, FF50, post-boot values |
| `test_cartridge.py` | 10 | MBC1/2/3/5 banking, RAM enable, MBC3 clock, saves |
| `test_display.py` | 2 | Palette shades and palette switching |
| `test_joypad.py` | script | P1 group selection and button bits; its checks run when pytest imports it |

### Differential tests and planted bugs

Each optimisation (timer fast path, dispatch table, dedicated handlers, HALT skip, lazy sync, frame loop) has a test that runs it against the straightforward code on random input and requires identical results. Each of these tests was checked by planting a small bug in the optimised path, such as an off-by-one in a cycle count or a missing interrupt check, and confirming that the test fails. When a planted bug went undetected, the test was strengthened. For example, the lazy-sync test now also compares when each I/O access happens inside its instruction.

## Test ROMs

`test_roms/` holds Blargg's test ROMs with their sources. `run_all_test_roms.py` runs seven of them and reads the result from the serial output: `cpu_instrs`, `03-op sp,hl`, `instr_timing`, `interrupt_time`, both `mem_timing`, and `halt_bug`. The ROMs report by printing "Passed" or "Failed". `interrupt_time` is expected to fail, because it needs Game Boy Color double speed.

The release results in the main README (all 33 non-sound Blargg ROMs, 111 mooneye ROMs, dmg-acid2) come from a separate harness that is not part of the repository. The mooneye ROMs and dmg-acid2 are not distributed here.

`test_with_blargg.py` is an early runner, kept for reference. It contains no pytest tests.
