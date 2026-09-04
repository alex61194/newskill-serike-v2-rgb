#!/usr/bin/env python3
"""
Newskill Serike TKL V2 - RGB Control

Protocol reverse-engineered from USB pcap:
  - HID Interface 1, Feature Report ID 0x06, 520 bytes
  - Sequence: INIT (0x84) -> CONFIG (0x04) -> APPLY (0x08 or 0x06)
  - Mode 0x08: 24-bit True RGB (378 bytes = 126 slots * 3 channels)
  - Mode 0x06: 4 additive RGB zones with 126-byte bitmaps
  - Endpoint: Col06 sub-device (vendor-defined 0xff00/0x0001)

Usage:
  python newskill_rgb.py list
  python newskill_rgb.py on
  python newskill_rgb.py off
  python newskill_rgb.py red
  python newskill_rgb.py hex FF8800
  python newskill_rgb.py rgb 255 100 0
  python newskill_rgb.py key 0 255 0 0
  python newskill_rgb.py test
"""

import sys
import time
import argparse
import struct

REPORT_ID = 0x06
REPORT_SIZE = 520
DEFAULT_VID = 0x05AC
DEFAULT_PID = 0x024F

# Hardware matrix LED positions (86 active keys mapped into 102 hardware slots)
V_LEDS = [
    0, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 96,
    1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85, 91, 97,
    2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62, 68, 74, 75, 86, 92, 98,
    3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63, 69, 81,
    4, 76, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 82, 94,
    5, 11, 17, 35, 53, 59, 65, 83, 89, 95, 101
]

# Exact INIT feature report (520 bytes)
INIT_REPORT = (
    b'\x06\x84\x00\x00\x01\x00\x80\x00' + b'\x00' * (REPORT_SIZE - 8)
)

# Exact CONFIG feature report (520 bytes)
CONFIG_REPORT = (
    b'\x06\x04\x00\x00\x01\x00\x80\x00'
    b'\x00\x03\x03\x01\x00\x00\x04\x04\x07\x01\x15\x20\x01\x00\x00\x00'
    b'\x00\x00\x01\x00\x04\x04\x00\xff\x04\x00\x00\x00\x00\x00\x00\x00'
    + b'\x00' * 24
    + b'\xff\xff'
    + b'\x04\x47' * 20
    + b'\x07\x47\x07\x47\x07\x44\x07\x44\x07\x44\x07\x44\x07\x44\x07\x44\x07\x44'
    + b'\x04\x04\x04\x04\x04\x04\x04\x04\x04\x04'
    + b'\x5a\xa5'
    + b'\x00' * (REPORT_SIZE - 136)
)


def get_hid_module():
    try:
        import hid
        return hid
    except ImportError:
        print("ERROR: 'hidapi' is required but not installed.")
        print("Install it with: py -m pip install hidapi   (or: pip install hidapi)")
        sys.exit(1)


def make_24bit_rgb_report(r, g, b, key_index=None):
    """Builds a 520-byte feature report using command 0x08 (24-bit TrueColor)."""
    report = bytearray(REPORT_SIZE)
    report[0] = REPORT_ID
    report[1] = 0x08
    report[4] = 0x01
    report[6] = 0x7A  # 378 bytes RGB (0x017A little-endian = 126 LEDs * 3)
    report[7] = 0x01

    if key_index is not None:
        idx = 8 + (key_index * 3)
        if idx + 2 < REPORT_SIZE:
            report[idx] = r
            report[idx + 1] = g
            report[idx + 2] = b
    else:
        for led in V_LEDS:
            idx = 8 + (led * 3)
            report[idx] = r
            report[idx + 1] = g
            report[idx + 2] = b

    return bytes(report)


def find_dev_path(hid_mod, vid, pid):
    for d in hid_mod.enumerate():
        if d['vendor_id'] != vid or d['product_id'] != pid:
            continue
        p = d['path']
        ps = p.decode(errors='ignore') if isinstance(p, bytes) else str(p)
        if 'Col06' in ps and 'MI_01' in ps:
            return p
    # Fallback to interface 1
    for d in hid_mod.enumerate():
        if d['vendor_id'] == vid and d['product_id'] == pid and d.get('interface_number') == 1:
            return d['path']
    return None


def send(dev, data):
    r = dev.send_feature_report(bytes(data))
    if r <= 0:
        print("  WARN: send returned %s" % r)
    return r


def set_color_24bit(dev, r, g, b, key_index=None):
    send(dev, INIT_REPORT)
    time.sleep(0.01)
    send(dev, CONFIG_REPORT)
    time.sleep(0.01)
    send(dev, make_24bit_rgb_report(r, g, b, key_index))
    time.sleep(0.01)


def parse_hex_color(hex_str):
    clean = hex_str.strip().lstrip('#')
    if len(clean) != 6:
        raise ValueError("Hex color must be 6 hex characters, e.g. #FF8800 or FF8800")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def main():
    parser = argparse.ArgumentParser(
        description='Newskill Serike TKL V2 RGB CLI Controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python newskill_rgb.py list
  python newskill_rgb.py on
  python newskill_rgb.py red
  python newskill_rgb.py hex #FF5500
  python newskill_rgb.py rgb 0 255 128
  python newskill_rgb.py key 0 255 0 0
  python newskill_rgb.py test
"""
    )
    parser.add_argument('action', nargs='?', default='list',
                        help='Action: list, on, off, red, green, blue, white, yellow, cyan, magenta, test, hex, rgb, key')
    parser.add_argument('params', nargs='*', help='Parameters for hex, rgb, or key action')
    parser.add_argument('--vid', type=lambda x: int(x, 16), default=DEFAULT_VID,
                        help=f'USB Vendor ID (default: 0x{DEFAULT_VID:04X})')
    parser.add_argument('--pid', type=lambda x: int(x, 16), default=DEFAULT_PID,
                        help=f'USB Product ID (default: 0x{DEFAULT_PID:04X})')
    args = parser.parse_args()

    hid_mod = get_hid_module()

    if args.action == 'list':
        print("Connected HID devices:")
        found = False
        for d in hid_mod.enumerate():
            v = d['vendor_id']
            p = d['product_id']
            prod = d.get('product_string', '') or '(none)'
            if v == args.vid and p == args.pid:
                print(f"  --> [MATCH] VID=0x{v:04x} PID=0x{p:04x} | Product: {prod} | Interface: {d.get('interface_number')}")
                found = True
            else:
                if 'newskill' in prod.lower() or 'keyboard' in prod.lower():
                    print(f"      VID=0x{v:04x} PID=0x{p:04x} | Product: {prod} | Interface: {d.get('interface_number')}")
        if not found:
            print(f"  Note: Target keyboard VID=0x{args.vid:04x} PID=0x{args.pid:04x} not matched in enumeration.")
        return

    path = find_dev_path(hid_mod, args.vid, args.pid)
    if not path:
        print(f"Device (0x{args.vid:04x}:0x{args.pid:04x}) not found.")
        print("Tip: If SignalRGB is running, close it before using direct HID control.")
        sys.exit(1)

    dev = hid_mod.device()
    try:
        dev.open_path(path)
    except Exception as e:
        print(f"Error opening HID device: {e}")
        print("Tip: SignalRGB holds an exclusive lock on the device while running.")
        sys.exit(1)

    named_colors = {
        'on': (255, 255, 255),
        'off': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
    }

    try:
        if args.action in named_colors:
            r, g, b = named_colors[args.action]
            print(f"Setting color to {args.action.upper()} RGB({r}, {g}, {b})")
            set_color_24bit(dev, r, g, b)
        elif args.action == 'hex':
            if not args.params:
                print("Usage: python newskill_rgb.py hex <HEX_CODE> (e.g. #FF8800)")
                sys.exit(1)
            r, g, b = parse_hex_color(args.params[0])
            print(f"Setting HEX #{args.params[0].lstrip('#')} -> RGB({r}, {g}, {b})")
            set_color_24bit(dev, r, g, b)
        elif args.action == 'rgb':
            if len(args.params) < 3:
                print("Usage: python newskill_rgb.py rgb <R> <G> <B> (e.g. 255 128 0)")
                sys.exit(1)
            r, g, b = int(args.params[0]), int(args.params[1]), int(args.params[2])
            print(f"Setting RGB({r}, {g}, {b})")
            set_color_24bit(dev, r, g, b)
        elif args.action == 'key':
            if not args.params:
                print("Usage: python newskill_rgb.py key <KEY_LED_INDEX> [R G B]")
                sys.exit(1)
            k_idx = int(args.params[0])
            r = int(args.params[1]) if len(args.params) > 1 else 255
            g = int(args.params[2]) if len(args.params) > 2 else 255
            b = int(args.params[3]) if len(args.params) > 3 else 255
            print(f"Setting LED index {k_idx} to RGB({r}, {g}, {b})")
            set_color_24bit(dev, r, g, b, key_index=k_idx)
        elif args.action == 'test':
            tests = [
                ('RED', 255, 0, 0), ('GREEN', 0, 255, 0), ('BLUE', 0, 0, 255),
                ('YELLOW', 255, 255, 0), ('CYAN', 0, 255, 255), ('MAGENTA', 255, 0, 255),
                ('WHITE', 255, 255, 255), ('OFF', 0, 0, 0)
            ]
            for name, r, g, b in tests:
                print(f"Test: {name}")
                set_color_24bit(dev, r, g, b)
                time.sleep(1.2)
        else:
            print(f"Unknown action: {args.action}")
            parser.print_help()
    finally:
        dev.close()


if __name__ == '__main__':
    main()
