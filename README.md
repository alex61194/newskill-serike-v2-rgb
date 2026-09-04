# Newskill Serike V2 TKL — SignalRGB Plugin & Python RGB Controller

[![Status](https://img.shields.io/badge/Status-Tested%20%26%20100%25%20Working-success.svg)]()
[![Hardware](https://img.shields.io/badge/Hardware-Newskill%20Serike%20V2%20TKL%20White-blue.svg)]()
[![Methodology](https://img.shields.io/badge/Built%20With-Vibecoding-purple.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

Custom **SignalRGB plugin** and standalone **Python CLI controller** for the **Newskill Serike V2 TKL** mechanical gaming keyboard (White / Ivory and Black editions).

> **Built with Vibecoding & Fully Tested on Real Hardware**  
> This entire project was built and reverse-engineered through **vibecoding** — extracting raw USB HID pcap packet captures, decoding the internal electrical matrix, bypassing firmware quirks, and engineering a zero-allocation render pipeline.  
> **100% Tested and Verified:** All 86 physical keys illuminate flawlessly with smooth 60 FPS SignalRGB canvas effects, without any keys dropping to the keyboard's default red fallback state.

---

## Table of Contents
1. [Hardware Specifications](#hardware-specifications)
2. [Step-by-Step: How the Plugin Works](#step-by-step-how-the-plugin-works)
   - [1. USB Endpoint Matching & Priority Override](#1-usb-endpoint-matching--priority-override)
   - [2. Hardware Initialization Handshake](#2-hardware-initialization-handshake)
   - [3. Hardware Electrical Matrix (102 Slots)](#3-hardware-electrical-matrix-102-slots)
   - [4. The "Keys Turning Red" Firmware Bug & Fix](#4-the-keys-turning-red-firmware-bug--the-virtual-grid-fix)
   - [5. Zero-Allocation 60 FPS Render Engine](#5-zero-allocation-60-fps-render-engine)
   - [6. Device Image & Metadata](#6-device-image--metadata)
3. [SignalRGB Plugin Installation](#signalrgb-plugin-installation)
4. [Python CLI Tool (`newskill_rgb.py`)](#python-cli-tool-newskill_rgbpy)
5. [Hardware Key Matrix Reference](#hardware-key-matrix-reference)
6. [License](#license)

---

## Hardware Specifications

| Property | Value |
| :--- | :--- |
| **Keyboard Model** | Newskill Serike V2 TKL (Tenkeyless, 86 keys, ISO-ES Spanish layout) |
| **USB Vendor ID (VID)** | `0x05AC` |
| **USB Product ID (PID)** | `0x024F` (shares default identifier with Apple Aluminium Keyboard) |
| **Target Interface** | Interface `1` |
| **HID Usage Page / Usage**| Usage Page `0xFF00`, Usage `0x0001` (Vendor-defined custom HID pipe) |
| **Report ID & Size** | Report ID `0x06`, Report Size: `520 bytes` |
| **Electrical Matrix** | 17 columns × 6 rows = 102 LED hardware slots ($6 \times \text{Col} + \text{Row}$) |

---

## Step-by-Step: How the Plugin Works

Understanding how this plugin drives the keyboard requires looking at how SignalRGB interacts with USB HID hardware and how the keyboard firmware operates:

```
+-------------------------------------------------------------+
|                     SignalRGB Canvas Engine                 |
|               (Generates 2D color coordinates)              |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|        buildGrid() (18x6 Continuous Virtual Grid)           |
|  - Prevents canvas coordinate gaps                          |
|  - Guarantees non-zero RGB sample stream                    |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|           Zero-Allocation Render Loop (60 FPS)              |
|  - Samples device.color(x, y) for all 86 keys               |
|  - In-place mutation into static 520-byte packet buffer     |
|  - Direct index write: packet[8 + (vLeds[i] * 3)]           |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|           HID Feature Report 0x06 (Command 0x08)            |
|  - Header: 06 08 00 00 01 00 7A 01 (378 bytes TrueColor)   |
|  - Direct 24-bit per-key RGB payload sent to Interface 1    |
+-------------------------------------------------------------+
```

### 1. USB Endpoint Matching & Priority Override
- **Endpoint Filter (`Validate`):**  
  The keyboard exposes multiple HID interfaces (standard keyboard endpoint, media consumer control, vendor-defined control pipe). The plugin strictly filters for Interface 1 with Usage Page `0xFF00` and Usage `0x0001`:
  ```javascript
  export function Validate(endpoint) {
      return endpoint.interface === 1 && endpoint.usage === 0x0001 && endpoint.usage_page === 0xFF00;
  }
  ```
- **Priority Override (`ZZZ_` prefix):**  
  Because the keyboard's internal controller inherits the USB PID `0x024F`, SignalRGB's generic built-in `SONIX_Keyboard_Controller.js` also attempts to claim the device. SignalRGB's `PluginCrawler` loads plugins in alphabetical order. Naming our plugin `ZZZ_Newskill_Serike_V2_TKL.js` guarantees it is processed **after** the Sonix controller, correctly registering Newskill as the authoritative driver.

### 2. Hardware Initialization Handshake
When SignalRGB loads or reloads the plugin, `Initialize()` runs a two-step handshake sequence:
1. **INIT Report (`0x84`):**  
   Sends `[0x06, 0x84, 0x00, 0x00, 0x01, 0x00, 0x80, 0x00, ...zeros to 520]` to wake up the internal LED controller and unlock direct streaming.
2. **CONFIG Report (`0x04`):**  
   Sends a 520-byte configuration frame configuring controller limits, profile settings, and disabling onboard animation cycling.

### 3. Hardware Electrical Matrix (102 Slots)
The physical keys are not wired sequentially from 0 to 85. Instead, the PCB features a 17-column by 6-row electrical circuit ($17 \times 6 = 102$ possible slots).
The hardware index for any LED is governed by:
$$\text{Hardware LED Index} = 6 \times \text{Column} + \text{Row}$$
- `vLeds`: An array of 86 integers mapping each physical key in logical order to its electrical index in the matrix.
- `vLedPositions`: An array of `[x, y]` coordinates mapping each physical key to its 2D physical position on the keyboard layout.

### 4. The "Keys Turning Red" Firmware Bug & The Virtual Grid Fix
- **The Problem:**  
  When earlier iterations tried to register only the 86 physical keys directly in `LedNames()` and `LedPositions()`, certain keys would randomly stop updating and fall back to the keyboard's factory default **static red** color.  
- **Root Cause:**  
  SignalRGB's canvas effect sampler interpolates colors across a continuous surface. When keys have sparse or non-continuous coordinate bounds, `device.color(x, y)` returns `[0, 0, 0]` for boundary positions. The Newskill keyboard firmware interprets `[0, 0, 0]` packets or empty updates as "signal lost", immediately reverting unaddressed LEDs to its internal red fallback profile.
- **The Solution:**  
  The plugin implements `buildGrid()` returning an 18×6 virtual canvas (108 points) for SignalRGB's layout registration. During the render pass, each physical key samples from its dedicated `vLedPositions[i]`, ensuring continuous color data is sent to every LED on every frame.

### 5. Zero-Allocation 60 FPS Render Engine
At 60 frames per second, creating arrays or concatenating buffers (`new Array()` or `array.concat()`) creates over **3,600 heap allocations per minute**, causing periodic garbage collection (GC) micro-stutters.

This plugin achieves **zero heap allocations** inside `Render()`:
```javascript
// Pre-allocated static 520-byte packet buffer in global scope
var packet = new Array(520).fill(0);
packet[0] = 0x06; // Report ID
packet[1] = 0x08; // 24-bit TrueColor Direct RGB Command
packet[4] = 0x01;
packet[6] = 0x7A; // 378 bytes payload (126 slots * 3 RGB channels, little-endian: 0x017A)
packet[7] = 0x01;

export function Render() {
    // Direct index mutation — 0 new allocations
    for (var i = 0; i < vLeds.length; i++) {
        var color = device.color(vLedPositions[i][0], vLedPositions[i][1]);
        var ledIdx = 8 + (vLeds[i] * 3);
        packet[ledIdx]     = color[0];
        packet[ledIdx + 1] = color[1];
        packet[ledIdx + 2] = color[2];
    }
    device.send_report(packet, 520);
    device.pause(1);
}
```

### 6. Device Image & Metadata
- **`DeviceType()`:** Returns `"keyboard"` so SignalRGB categorizes it cleanly under the Keyboards section.
- **`ConflictingProcesses()`:** Declares OEM utilities (`["Newskill.exe", "Serike.exe"]`) to prevent USB bus collisions.
- **`ImageUrl()`:** Links directly to the official high-resolution, transparent-background top-down render of the **Newskill Serike V2 TKL White (Ivory)**.

---

## SignalRGB Plugin Installation

1. Copy `ZZZ_Newskill_Serike_V2_TKL.js` to your SignalRGB user plugins folder:
   ```
   %USERPROFILE%\Documents\WhirlwindFX\Plugins\Newskill\
   ```
   *(Create the `Newskill` directory if it does not already exist).*

2. Restart SignalRGB (or reload plugins from Settings).
3. The keyboard will appear in the **Devices** tab as **Newskill Serike V2 TKL** with its official white render.
4. **Configurable Settings in SignalRGB:**
   - **Lighting Mode:** `Canvas` (default, reactive RGB effects) or `Forced` (static solid color).
   - **Forced Color:** Choose any color when in Forced mode.
   - **Shutdown Color:** Color applied when the PC is sleeping, locked, or shutting down.

---

## Python CLI Tool (`newskill_rgb.py`)

A standalone, dependency-light Python script to control the keyboard's RGB directly from the command line without SignalRGB.

### Requirements
```bash
pip install hidapi
# or on Windows: py -m pip install hidapi
```

### Usage
```bash
# List connected HID devices (auto-matches VID 0x05AC / PID 0x024F)
python newskill_rgb.py list

# Full keyboard on / off
python newskill_rgb.py on
python newskill_rgb.py off

# Named colors
python newskill_rgb.py red
python newskill_rgb.py green
python newskill_rgb.py blue
python newskill_rgb.py cyan
python newskill_rgb.py magenta
python newskill_rgb.py yellow
python newskill_rgb.py white

# Custom HEX color
python newskill_rgb.py hex #FF5500
python newskill_rgb.py hex 00FFAA

# Custom RGB values (0-255)
python newskill_rgb.py rgb 255 128 0

# Individual key LED test (key index 0 to 101)
python newskill_rgb.py key 0 255 0 0

# Automated RGB color cycle test
python newskill_rgb.py test
```

> **Note:** If SignalRGB is running, it maintains an exclusive USB handle on Interface 1. Close SignalRGB before running `newskill_rgb.py`.

---

## Hardware Key Matrix Reference

The 86 keys map to the 102-slot matrix as follows:

| Row | Keys | Matrix Indices (`vLeds`) |
| :--- | :--- | :--- |
| **Row 0** | Esc, F1–F12, Mute | `0, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 96` |
| **Row 1** | \`, 1–0, -, =, Backspace, Ins, Home, PgUp | `1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85, 91, 97` |
| **Row 2** | Tab, Q–P, [, ], \\, Del, End, PgDn | `2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62, 68, 74, 75, 86, 92, 98` |
| **Row 3** | CapsLock, A–L, ;, ', Enter | `3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63, 69, 81` |
| **Row 4** | LShift, ISO \\<, Z–M, ,, ., /, RShift, Up | `4, 76, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 82, 94` |
| **Row 5** | LCtrl, LWin, LAlt, Space, RAlt, Fn, Menu, RCtrl, Left, Down, Right | `5, 11, 17, 35, 53, 59, 65, 83, 89, 95, 101` |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
