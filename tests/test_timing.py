"""Per-access timing and OAM DMA (Pan Docs "OAM DMA Transfer"; mooneye oam_dma_*)."""

from src.cpu import CPU


def _cpu(program, at=0xC000):
    cpu = CPU()
    cpu.memory.load_rom(bytes(0x8000))
    cpu.simulate_boot()
    cpu.memory._data[0xFF40] = 0x00          # LCD off: OAM only locked by DMA
    cpu.memory._data[at:at + len(program)] = bytes(program)
    cpu.registers._pc = at
    cpu.registers._sp = 0xDFF0
    return cpu


def test_dma_blocks_oam_for_160_cycles_after_one_setup_cycle():
    # ldh (DMA),a at cycle W; then NOPs. OAM reads 0xFF from W+2 to W+161.
    cpu = _cpu([0xE0, 0x46] + [0x00] * 200)
    cpu.memory._data[0x8000:0x80A0] = bytes(range(160))
    cpu.registers._a = 0x80
    cpu.step()                                # the write happens in this instruction's 3rd cycle
    mem = cpu.memory
    states = []
    for _ in range(165):
        states.append(mem.read_byte(0xFE05))
        cpu.step()                            # one NOP = one M-cycle
    # write in cycle W: W+1 is a free setup cycle, W+2..W+161 are blocked
    blocked = [i for i, v in enumerate(states) if v == 0xFF]
    assert blocked == list(range(1, 161))
    assert mem.read_byte(0xFE05) == 5         # copy landed


def test_dma_source_e0_and_up_reads_work_ram():
    cpu = _cpu([0xE0, 0x46] + [0x00] * 170)
    cpu.memory._data[0xDE00:0xDEA0] = bytes([0x5A] * 160)
    cpu.registers._a = 0xFE                   # 0xFE00 -> work RAM 0xDE00
    for _ in range(170):
        cpu.step()
    assert cpu.memory.read_byte(0xFE00) == 0x5A


def test_dma_does_not_add_cycles_to_the_cpu():
    cpu = _cpu([0xE0, 0x46, 0x00])
    cpu.registers._a = 0x80
    before = cpu.total_cycles
    cpu.step()
    assert cpu.total_cycles - before == 12


def test_timer_read_sees_its_own_cycle():
    """ld a,(nn) reads in its 4th cycle; with the 16-cycle timer rate, TIMA
    read that way must agree with ldh a,(n) one NOP later (both read on the
    same hardware cycle)."""
    def tima_after(program):
        cpu = _cpu(program)
        cpu._system_counter = 0
        cpu.memory._data[0xFF05] = 0
        cpu.memory._data[0xFF07] = 0x05       # enabled, every 4 M-cycles
        for _ in range(len([b for b in program if b == 0x00]) + 1):
            cpu.step()
        return cpu.registers._a
    ld_nn = [0x00, 0x00, 0xFA, 0x05, 0xFF]    # NOP NOP; LD A,(FF05)
    ldh = [0x00, 0x00, 0x00, 0xF0, 0x05]      # NOP NOP NOP; LDH A,(05)
    for extra in range(4):
        assert tima_after([0x00] * extra + ld_nn) == tima_after([0x00] * extra + ldh)


def test_serial_transfer_takes_8_bits_of_the_8192_hz_clock():
    cpu = _cpu([0x00] * 2000)
    mem = cpu.memory
    cpu._system_counter = 0
    mem.write_byte(0xFF0F, 0x00)
    mem.write_byte(0xFF01, 0x42)
    mem.write_byte(0xFF02, 0x81)              # start, internal clock
    steps = 0
    while mem.read_byte(0xFF02) & 0x80:
        cpu.step()
        steps += 1
    assert steps == 8 * 128                   # 8 bits x 512 T-cycles, in 1-M-cycle NOPs
    assert mem.read_byte(0xFF01) == 0xFF      # nothing connected: 1s shifted in
    assert mem.read_byte(0xFF0F) & 0x08       # serial interrupt


def test_serial_with_external_clock_never_finishes():
    cpu = _cpu([0x00] * 1500)
    cpu.memory.write_byte(0xFF02, 0x80)
    for _ in range(1500):
        cpu.step()
    assert cpu.memory.read_byte(0xFF02) & 0x80


def test_joypad_interrupt_only_for_selected_group():
    cpu = _cpu([0x00])
    mem = cpu.memory
    mem.write_byte(0xFF0F, 0x00)
    mem.write_byte(0xFF00, 0x20)              # select directions only
    mem.joypad.press_button("a")
    assert not mem.read_byte(0xFF0F) & 0x10
    mem.joypad.press_button("left")
    assert mem.read_byte(0xFF0F) & 0x10
    mem.write_byte(0xFF0F, 0x00)
    mem.write_byte(0xFF00, 0x10)              # now select buttons: A is held -> edge
    assert mem.read_byte(0xFF0F) & 0x10
