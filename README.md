# Newskill Serike V2 TKL — RGB Control

SignalRGB plugin and Python script to control the RGB lighting of the **Newskill Serike V2 TKL** keyboard.

> Built with vibecoding — protocol reverse-engineered from USB pcap captures.

## Hardware

- **Keyboard:** Newskill Serike V2 TKL (86 keys, Tenkeyless form factor)
- **VID/PID:** `0x05AC:0x024F` (inherits ID from Apple Aluminium Keyboard ANSI)
- **HID Interface:** Interface 1, Usage Page `0xFF00`, Usage `0x0001` (vendor-defined)
- **Report ID:** `0x06`, report size: 520 bytes
- **Matrix Layout:** 17 columns × 6 rows = 102 hardware LED slots ($6 \times \text{Col} + \text{Row}$), with 86 physical keys mapped.

## Protocol (reverse-engineered from USB pcap)

The keyboard uses HID **Feature Reports** over Interface 1 with a 3-step sequence:

### 1. INIT (`0x84`)
Initializes the RGB controller. Must always be sent first.

```
06 84 00 00 01 00 80 00 + zeros up to 520 bytes
```

### 2. CONFIG (`0x04`)
Configures internal controller parameters (color mode, brightness, profile, etc.).

```
06 04 00 00 01 00 80 00 + 128 bytes config + zeros
```

### 3. APPLY (`0x08` TrueColor RGB / `0x06` Bitmap Zones)
- **Mode `0x08` (Direct 24-bit TrueColor):**
  Header: `06 08 00 00 01 00 7A 01` (0x017A little-endian = 378 bytes = 126 slots × 3 RGB channels) + zeros.
  Allows setting arbitrary 24-bit color per key. Used by SignalRGB.
- **Mode `0x06` (Additive Zones):**
  Header: `06 06 00 00 01 00 80 01` + 4 additive zones of 126-byte bitmaps (Red, Green, Blue, Unused).

## Files

| File | Description |
|------|-------------|
| `Newskill_Serike_V2_TKL.js` / `ZZZ_Newskill_Serike_V2_TKL.js` | **SignalRGB** plugin — per-key LED mapping, zero-allocation rendering, gamma curve, and HID reports |
| `newskill_rgb.py` | Standalone **Python** script for CLI RGB control (named colors, hex, rgb, per-key test) |

## SignalRGB Plugin

### Installation
1. Copy `ZZZ_Newskill_Serike_V2_TKL.js` to:
   ```
   %USERPROFILE%\Documents\WhirlwindFX\Plugins\Newskill\
   ```
   *(Note: The `ZZZ_` prefix is required because SignalRGB's built-in `SONIX_Keyboard_Controller.js` also claims PID `0x024F`. The `ZZZ_` prefix ensures our plugin is crawled last and takes precedence).*
2. Restart or reload SignalRGB — the keyboard will be detected as **Newskill Serike V2 TKL** under Keyboards.
3. Plugin settings in SignalRGB:
   - **Lighting Mode:** `Canvas` (active effects) or `Forced` (solid color)
   - **Forced Color:** solid color when forced mode is active
   - **Shutdown Color:** color when the PC is suspended or turned off

### Key Architecture Features
- **Zero Allocations per Frame:** Pre-allocated 520-byte packet buffer, avoiding GC micro-stutters and heap fragmentation at 60 FPS.
- **Continuous 18x6 Sampling Surface:** Avoids SignalRGB canvas holes that return [0,0,0], preventing the firmware from dropping into its default red static fallback.
- **Hardware Matrix Mapping:** 1:1 mapping of physical key locations to the 102 hardware LED slots ($6 \times \text{Col} + \text{Row}$).
- **Device Classification:** Declares `export function DeviceType() { return "keyboard"; }` for proper category placement in SignalRGB.
- **TKL Device Image:** Provides thumbnail rendering for UI layout.
- **Conflict Management:** Declares `export function ConflictingProcesses()` for Newskill OEM software.

## Python Script

### Requirements
```bash
pip install hidapi
# or: py -m pip install hidapi
```

### Usage
```bash
# List connected HID devices (defaults to VID 0x05ac, PID 0x024f)
python newskill_rgb.py list

# Turn all keys on (white) or off
python newskill_rgb.py on
python newskill_rgb.py off

# Standard named colors
python newskill_rgb.py red
python newskill_rgb.py green
python newskill_rgb.py blue

# Any arbitrary HEX color
python newskill_rgb.py hex #FF5500
python newskill_rgb.py hex 00FFAA

# Any arbitrary RGB values (0-255)
python newskill_rgb.py rgb 255 128 0

# Test an individual key switch LED (0-101)
python newskill_rgb.py key 0 255 0 0

# Automated color cycle test
python newskill_rgb.py test
```

> **Note:** If SignalRGB is running, it holds an exclusive lock on the USB HID interface. Close SignalRGB before running direct commands with `newskill_rgb.py`.

## License

MIT
