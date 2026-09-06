export function Name() { return "Newskill Serike V2 TKL"; }
export function VendorId() { return 0x05ac; }
export function ProductId() { return 0x024f; }
export function Publisher() { return "WhirlwindFX"; }
export function Documentation() { return "troubleshooting/brand"; }
export function DeviceType() { return "keyboard"; }
export function Size() { return [18, 6]; }
export function DefaultPosition() { return [100, 50]; }
export function DefaultScale() { return 8.0; }
export function ConflictingProcesses() { return ["Newskill.exe", "Serike.exe"]; }
export function ImageUrl() { return "https://cdn.shopify.com/s/files/1/0986/3498/9907/files/fotosserikev2TKL1800x1800_08IVORY.png"; }

/* global
shutdownColor:readonly
LightingMode:readonly
forcedColor:readonly
*/
export function ControllableParameters() {
    return [
        {
            property: "shutdownColor",
            group: "lighting",
            label: "Shutdown Color",
            description: "Color applied when the system is shutting down or suspending",
            min: "0",
            max: "360",
            type: "color",
            default: "#000000"
        },
        {
            property: "LightingMode",
            group: "lighting",
            label: "Lighting Mode",
            description: "Canvas pulls colors from the active effect; Forced uses the solid color below",
            type: "combobox",
            values: ["Canvas", "Forced"],
            default: "Canvas"
        },
        {
            property: "forcedColor",
            group: "lighting",
            label: "Forced Color",
            description: "The color used when Forced lighting mode is enabled",
            min: "0",
            max: "360",
            type: "color",
            default: "#009bde"
        }
    ];
}

var vLedNames = [
    "Esc","F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12","Mute",
    "`","1","2","3","4","5","6","7","8","9","0","-","=","Backspace","Insert","Home","Page Up",
    "Tab","Q","W","E","R","T","Y","U","I","O","P","[","]","\\","Del","End","Page Down",
    "Caps Lock","A","S","D","F","G","H","J","K","L",";","'","Enter",
    "Left Shift","ISO_<","Z","X","C","V","B","N","M",",",".","/","Right Shift","Up Arrow",
    "Left Ctrl","Left Win","Left Alt","Space","Right Alt","Fn","Menu","Right Ctrl","Left Arrow","Down Arrow","Right Arrow"
];

function buildGrid() {
    var names = [], positions = [];
    for (var y = 0; y < 6; y++) {
        for (var x = 0; x < 18; x++) {
            names.push(x + "," + y);
            positions.push([x, y]);
        }
    }
    return [names, positions];
}

var gridData = buildGrid();

export function LedNames() { return gridData[0]; }
export function LedPositions() { return gridData[1]; }

export function Initialize() {
    sendInit();
    sendConfig();
}

var vLeds = [
    0, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 96,
    1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85, 91, 97,
    2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62, 68, 74, 75, 86, 92, 98,
    3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63, 69, 81,
    4, 76, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 82, 94,
    5, 11, 17, 35, 53, 59, 65, 83, 89, 95, 101
];

var vLedPositions = [
    [0,0],[2,0],[3,0],[4,0],[5,0],[7,0],[8,0],[9,0],[10,0],[11,0],[12,0],[13,0],[14,0],[17,0],
    [0,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1],[8,1],[9,1],[10,1],[11,1],[12,1],[13,1],[15,1],[16,1],[17,1],
    [0,2],[1,2],[2,2],[3,2],[4,2],[5,2],[6,2],[7,2],[8,2],[9,2],[10,2],[11,2],[12,2],[13,2],[15,2],[16,2],[17,2],
    [0,3],[1,3],[2,3],[3,3],[4,3],[5,3],[6,3],[7,3],[8,3],[9,3],[10,3],[11,3],[12,3],
    [0,4],[1,4],[2,4],[3,4],[4,4],[5,4],[6,4],[7,4],[8,4],[9,4],[10,4],[11,4],[12,4],[16,4],
    [0,5],[1,5],[2,5],[6,5],[7,5],[8,5],[9,5],[10,5],[15,5],[16,5],[17,5]
];

var packet = new Array(520).fill(0);
packet[0] = 0x06;
packet[1] = 0x08;
packet[4] = 0x01;
packet[6] = 0x7A; // 378 bytes RGB (126 LEDs * 3, little-endian)
packet[7] = 0x01;

var _lastForced = "";
var _cachedForced = [0, 0, 0];

export function Render() {
    var i, color, r, g, b, ledIdx;

    if (LightingMode === "Forced") {
        if (forcedColor !== _lastForced) {
            _cachedForced = hexToRgb(forcedColor);
            _lastForced = forcedColor;
        }
        r = _cachedForced[0];
        g = _cachedForced[1];
        b = _cachedForced[2];
        for (i = 0; i < vLeds.length; i++) {
            ledIdx = 8 + (vLeds[i] * 3);
            packet[ledIdx]     = r;
            packet[ledIdx + 1] = g;
            packet[ledIdx + 2] = b;
        }
    } else {
        for (i = 0; i < vLeds.length; i++) {
            color = device.color(vLedPositions[i][0], vLedPositions[i][1]);
            ledIdx = 8 + (vLeds[i] * 3);
            packet[ledIdx]     = color[0];
            packet[ledIdx + 1] = color[1];
            packet[ledIdx + 2] = color[2];
        }
    }

    device.send_report(packet, 520);
    device.pause(1);
}

export function Shutdown(SystemSuspending) {
    var color = SystemSuspending ? [0, 0, 0] : hexToRgb(shutdownColor);
    var i, ledIdx;
    for (i = 0; i < vLeds.length; i++) {
        ledIdx = 8 + (vLeds[i] * 3);
        packet[ledIdx]     = color[0];
        packet[ledIdx + 1] = color[1];
        packet[ledIdx + 2] = color[2];
    }
    device.send_report(packet, 520);
    device.pause(1);
}

export function Validate(endpoint) {
    return endpoint.interface === 1 && endpoint.usage === 0x0001 && endpoint.usage_page === 0xFF00;
}

function sendInit() {
    var initPacket = new Array(520).fill(0);
    initPacket[0] = 0x06;
    initPacket[1] = 0x84;
    initPacket[4] = 0x01;
    initPacket[6] = 0x80;
    device.send_report(initPacket, 520);
    device.pause(10);
}

function sendConfig() {
    var configPacket = new Array(520).fill(0);
    var header = [
        0x06, 0x04, 0x00, 0x00, 0x01, 0x00, 0x80, 0x00,
        0x00, 0x03, 0x03, 0x01, 0x00, 0x00, 0x04, 0x04, 0x07, 0x01, 0x15, 0x20, 0x01, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x04, 0x04, 0x00, 0xff, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ];
    for (var i = 0; i < header.length; i++) { configPacket[i] = header[i]; }

    var idx = 64;
    configPacket[idx++] = 0xff;
    configPacket[idx++] = 0xff;

    for (var j = 0; j < 20; j++) {
        configPacket[idx++] = 0x04;
        configPacket[idx++] = 0x47;
    }

    var tail = [
        0x07, 0x47, 0x07, 0x47, 0x07, 0x44, 0x07, 0x44, 0x07, 0x44, 0x07, 0x44, 0x07, 0x44, 0x07, 0x44, 0x07, 0x44,
        0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04,
        0x5a, 0xa5
    ];
    for (var k = 0; k < tail.length; k++) { configPacket[idx++] = tail[k]; }

    device.send_report(configPacket, 520);
    device.pause(10);
}

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : [0, 0, 0];
}
