# Newskill Serike V2 TKL — RGB Control

SignalRGB plugin and Python script to control the RGB lighting of the **Newskill Serike V2 TKL** keyboard.

> Built with vibecoding — protocol reverse-engineered from USB pcap captures.

## Hardware

- **Keyboard:** Newskill Serike V2 TKL (86 keys, Tenkeyless form factor)
- **VID/PID:** `0x05AC:0x024F` (inherits ID from Apple Aluminium Keyboard ANSI)
- **HID Interface:** Interface 1, Usage Page `0xFF00`, Usage `0x0001` (vendor-defined)
- **Report ID:** `0x06`, report size: 520 bytes

## Protocol (reverse-engineered from USB pcap)

The keyboard uses HID **Feature Reports** over Interface 1 with a 3-step sequence:

### 1. INIT (`0x84`)
Initializes the RGB controller. Must always be sent first.

```
06 84 00 00 01 00 80 00 + zeros up to 520 bytes
```

### 2. CONFIG (`0x04`)
Configures internal controller parameters (color mode, brightness, etc.).

```
06 04 00 00 01 00 80 00 + 128 bytes config + zeros
```

### 3. APPLY (`0x06`)
Applies colors per zone. There are **4 additive RGB zones**:
- **Zone 0:** Red — offset `0x08`
- **Zone 1:** Green — offset `0x86` (134)
- **Zone 2:** Blue — offset `0x104` (260)
- **Zone 3:** Offset `0x182` (386, unused)

Each zone has a **126-byte bitmap** where `0xFF` = key ON and `0x00` = OFF.
Colors are **additive**: enabling red + green zones = yellow.

APPLY header:
```
06 06 00 00 01 00 80 01
```

Header + 306 bytes RGB (102 positions × 3 channels).

## Files

| File | Description |
|------|-------------|
| `Newskill_Serike_V2_TKL.js` | **SignalRGB** plugin — LED mapping, rendering, and HID report sending |
| `newskill_rgb.py` | Standalone **Python** script for CLI RGB control |

## SignalRGB Plugin

### Installation
1. Copy `Newskill_Serike_V2_TKL.js` to:
   ```
   %USERPROFILE%\Documents\WhirlwindFX\Plugins\Newskill\
   ```
2. Open SignalRGB — the keyboard should be detected automatically
3. Plugin settings:
   - **Lighting Mode:** `Canvas` (colors from SignalRGB) or `Forced` (fixed color)
   - **Forced Color:** color when mode is `Forced`
   - **Shutdown Color:** color when PC shuts down

### How it works
```javascript
// 102 LEDs mapped to 86 physical keys
var vLeds = [0, 12, 18, ..., 101];
var vLedPositions = [[0,0], [2,0], ..., [17,5]];

// On each frame (Render):
// 1. Gets each key's color from SignalRGB canvas
// 2. Builds a 306-byte RGB array (102 LEDs × 3)
// 3. Sends a 520-byte HID feature report to the keyboard
// 4. LEDs are distributed across columns (0-17) and rows (0-6)

// The TKL layout is defined in vLedNames with 86 key names
```

### Device validation
The plugin only activates on the correct endpoint:
```javascript
endpoint.interface === 1 &&
endpoint.usage === 0x0001 &&
endpoint.usage_page === 0xFF00
```

## Python Script

### Requirements
```bash
pip install hidapi
```

### Usage
```bash
# List available HID devices
python newskill_rgb.py list

# Turn all keys white
python newskill_rgb.py on --vid 0x05ac --pid 0x024f

# Turn all keys off
python newskill_rgb.py off --vid 0x05ac --pid 0x024f

# Basic colors
python newskill_rgb.py red --vid 0x05ac --pid 0x024f
python newskill_rgb.py green --vid 0x05ac --pid 0x024f
python newskill_rgb.py blue --vid 0x05ac --pid 0x024f

# Color cycle test (1.5s each)
python newskill_rgb.py test --vid 0x05ac --pid 0x024f
```

### How it works
1. Finds the HID device by VID/PID and sub-device `Col06` + `MI_01`
2. Sends INIT → CONFIG → APPLY in sequence
3. APPLY uses 4 zones of 126 bytes each:
   - Zone 0 (Red): key bitmap for red channel
   - Zone 1 (Green): key bitmap for green channel
   - Zone 2 (Blue): key bitmap for blue channel
4. Only the 86 bits from the TKL bitmap are active; the rest are `0x00`

## License

MIT
