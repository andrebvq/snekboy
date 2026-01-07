# Joypad Implementation

## Overview

Implemented full Game Boy joypad support (P1 register at 0xFF00) with keyboard input mapping.

## Implementation

### Files Created/Modified

1. **src/joypad.py** (NEW)
   - Complete joypad controller implementation
   - Handles P1 register read/write
   - Manages button states
   - Triggers joypad interrupts

2. **src/memory.py** (MODIFIED)
   - Added joypad instance
   - P1 register (0xFF00) read/write handling
   - Joypad interrupt callback integration

3. **src/display.py** (MODIFIED)
   - Keyboard event handling (KEYDOWN/KEYUP)
   - Button press/release on key events
   - Passes joypad instance to event handler

4. **src/emulator.py** (MODIFIED)
   - Passes joypad to display.handle_events()
   - Shows control scheme on startup

## Keyboard Mapping

### Buttons
- **A**: A key
- **B**: S key
- **Start**: Z key
- **Select**: X key

### D-Pad
- **Up**: I key
- **Down**: K key
- **Left**: J key
- **Right**: L key

### System
- **Quit**: ESC key

## P1 Register (0xFF00)

### Bit Layout
```
Bit 7-6: Not used (always 1)
Bit 5:   P15 Select Button Keys (0=Select)
Bit 4:   P14 Select Direction Keys (0=Select)
Bit 3:   P13 Input Down or Start (0=Pressed)
Bit 2:   P12 Input Up or Select (0=Pressed)
Bit 1:   P11 Input Left or B (0=Pressed)
Bit 0:   P10 Input Right or A (0=Pressed)
```

### Reading Buttons
1. Game writes to P1 to select button group:
   - Write with bit 5=0: Select A/B/Start/Select
   - Write with bit 4=0: Select D-Pad
2. Game reads P1 to get button states (bits 0-3)
3. 0 = pressed, 1 = not pressed (inverted logic)

## Interrupts

- Joypad interrupt (bit 4 of IF register) is triggered when any button is pressed
- Game can enable joypad interrupt via IE register (bit 4)
- Used to wake from HALT or handle input immediately

## Testing

Created `tests/test_joypad.py`:
- Tests P1 register read/write
- Tests button press/release
- Tests button group selection
- Tests multiple simultaneous buttons
- All tests pass

## How It Works

1. User presses keyboard key
2. Display.handle_events() detects KEYDOWN event
3. Calls joypad.press_button() for corresponding button
4. Joypad triggers interrupt via callback
5. Updates internal button state
6. Game reads P1 register to check button states

## Usage

```bash
python -m src.emulator
```

Then use the keyboard to control the game:
- Press Z to start Tetris
- Use I/K/J/L to move pieces
- Press A to rotate
- Press K to drop faster

## Next Steps

With joypad support, Tetris should now:
- Wake from wait loops
- Show title screen
- Respond to Start button
- Be fully playable!
