#!/usr/bin/env python3
"""
Newskill Serike TKL V2 - RGB Control

Protocol reverse-engineered from USB pcap:
  - HID Interface 1, Feature Report ID 0x06, 520 bytes
  - Sequence: INIT (0x84) -> CONFIG (0x04) -> APPLY (0x06)
  - Zones: 0=Red, 1=Green, 2=Blue (additive)
  - Each zone has 126-byte bitmap: 0xff=ON, 0x00=OFF
  - Must open Col06 sub-device (vendor-defined 0xff00/0x0001)

Usage:
  python newskill_rgb.py list
  python newskill_rgb.py on --vid 0x05ac --pid 0x024f
  python newskill_rgb.py off --vid 0x05ac --pid 0x024f
  python newskill_rgb.py red --vid 0x05ac --pid 0x024f
  python newskill_rgb.py test --vid 0x05ac --pid 0x024f
"""

import sys
import time
import argparse
import struct

try:
    import hid
except ImportError:
    print("ERROR: hidapi not installed. Run: pip install hidapi")
    sys.exit(1)

REPORT_ID = 0x06
REPORT_SIZE = 520
ZONE_OFFSETS = [8, 134, 260, 386]

# Exact TKL bitmap (126 bytes, 86 keys active)
TKL_BITMAP = bytes([
    0xff,0xff,0xff,0xff,0xff,0xff,0x00,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x00,0xff,0xff,0xff,0xff,0xff,0x00,0xff,0xff,
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x00,0xff,0xff,0xff,0xff,0xff,0x00,
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
    0xff,0xff,0xff,0xff,0xff,0xff,0x00,0x00,0xff,0xff,0xff,0xff,0xff,0x00,0xff,0xff,
    0x00,0xff,0xff,0xff,0x00,0xff,0xff,0x00,0x00,0xff,0x00,0xff,0xff,0x00,0xff,0xff,
    0xff,0xff,0xff,0x00,0x00,0xff,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
])

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

# Template APPLY report (zone 0 with bitmap, others zeroed)
def make_apply_report(z0=None, z1=None, z2=None, z3=None):
    report = bytearray(REPORT_SIZE)
    report[0] = REPORT_ID
    report[1] = 0x06
    report[4] = 0x01
    report[6] = 0x80
    report[7] = 0x01
    zones = [z0, z1, z2, z3]
    for i, zdata in enumerate(zones):
        if zdata:
            zoff = ZONE_OFFSETS[i]
            report[zoff:zoff + len(zdata)] = zdata[:126]
    return bytes(report)


def find_dev_path(vid, pid):
    for d in hid.enumerate():
        if d['vendor_id'] != vid or d['product_id'] != pid:
            continue
        p = d['path']
        ps = p.decode() if isinstance(p, bytes) else str(p)
        if 'Col06' in ps and 'MI_01' in ps:
            return p
    return None


def send(dev, data):
    r = dev.send_feature_report(bytes(data))
    if r <= 0:
        print("  WARN: send returned %s" % r)
    return r


def set_color(dev, r, g, b):
    send(dev, INIT_REPORT)
    time.sleep(0.01)
    send(dev, CONFIG_REPORT)
    time.sleep(0.01)
    z0 = TKL_BITMAP if r else None
    z1 = TKL_BITMAP if g else None
    z2 = TKL_BITMAP if b else None
    send(dev, make_apply_report(z0, z1, z2))
    time.sleep(0.01)


def main():
    parser = argparse.ArgumentParser(description='Newskill Serike TKL V2 RGB')
    parser.add_argument('action', nargs='?', default='list',
                        choices=['list', 'on', 'off', 'red', 'green', 'blue',
                                 'white', 'yellow', 'cyan', 'magenta', 'test'])
    parser.add_argument('--vid', type=lambda x: int(x, 16))
    parser.add_argument('--pid', type=lambda x: int(x, 16))
    args = parser.parse_args()

    if args.action == 'list':
        for d in hid.enumerate():
            print('VID=0x%04x PID=0x%04x' % (d['vendor_id'], d['product_id']))
            print('  Product:   %s' % (d.get('product_string', '') or '(none)'))
            print('  MFR:       %s' % (d.get('manufacturer_string', '') or '(none)'))
            print('  Interface: %d' % d.get('interface_number', -1))
        return

    if not args.vid or not args.pid:
        print('ERROR: --vid and --pid required.')
        sys.exit(1)

    path = find_dev_path(args.vid, args.pid)
    if not path:
        print('Device not found. Try running "list" first.')
        sys.exit(1)

    dev = hid.device()
    try:
        dev.open_path(path)
    except Exception as e:
        print('Error: %s' % e)
        sys.exit(1)

    colors = {
        'on': (255, 255, 255), 'off': (0, 0, 0),
        'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0), 'cyan': (0, 255, 255), 'magenta': (255, 0, 255),
    }

    try:
        if args.action in colors:
            r, g, b = colors[args.action]
            if r == g == b == 0:
                print('OFF')
            else:
                print('RGB(%d,%d,%d)' % (r, g, b))
            set_color(dev, r, g, b)
        elif args.action == 'test':
            tests = [('RED', 255,0,0), ('GREEN', 0,255,0), ('BLUE', 0,0,255),
                     ('WHITE', 255,255,255), ('YELLOW', 255,255,0),
                     ('CYAN', 0,255,255), ('MAGENTA', 255,0,255), ('OFF', 0,0,0)]
            for name, r, g, b in tests:
                print(name)
                set_color(dev, r, g, b)
                time.sleep(1.5)
    finally:
        dev.close()


if __name__ == '__main__':
    main()
