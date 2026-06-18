export function Name() { return "Newskill Serike V2 TKL"; }
export function VendorId() { return 0x05ac; }
export function ProductId() { return 0x024f; }
export function Publisher() { return "WhirlwindFX"; }
export function Documentation() { return "troubleshooting/brand"; }
export function Size() { return [18, 7]; }
export function DefaultPosition() { return [100, 50]; }
export function DefaultScale() { return 8.0; }

export function ControllableParameters() {
    return [
        {property:"shutdownColor", group:"lighting", label:"Shutdown Color", min:"0", max:"360", type:"color", default:"#000000"},
        {property:"LightingMode", group:"lighting", label:"Lighting Mode", type:"combobox", values:["Canvas", "Forced"], default:"Canvas"},
        {property:"forcedColor", group:"lighting", label:"Forced Color", min:"0", max:"360", type:"color", default:"#009bde"},
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

export function LedNames() { return ["All"]; }
export function LedPositions() { return [[9,3]]; }

export function Initialize() {}

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

export function Render() {
    var RGBData = new Array(306).fill(0);

    for (var i = 0; i < vLeds.length; i++) {
        var color;
        if (LightingMode === "Forced") {
            color = hexToRgb(forcedColor);
        } else {
            color = device.color(vLedPositions[i][0], vLedPositions[i][1]);
        }
        RGBData[(vLeds[i]*3)]   = color[0];
        RGBData[(vLeds[i]*3)+1] = color[1];
        RGBData[(vLeds[i]*3)+2] = color[2];
    }

    var packet = [0x06, 0x08, 0x00, 0x00, 0x01, 0x00, 0x7A, 0x01];
    packet = packet.concat(RGBData);
    device.send_report(packet, 520);
    device.pause(1);
}

export function Shutdown(SystemSuspending) {
    var color = SystemSuspending ? [0,0,0] : hexToRgb(shutdownColor);
    var RGBData = new Array(306).fill(0);

    for (var i = 0; i < vLeds.length; i++) {
        RGBData[(vLeds[i]*3)]   = color[0];
        RGBData[(vLeds[i]*3)+1] = color[1];
        RGBData[(vLeds[i]*3)+2] = color[2];
    }

    var packet = [0x06, 0x08, 0x00, 0x00, 0x01, 0x00, 0x7A, 0x01];
    packet = packet.concat(RGBData);
    device.send_report(packet, 520);
    device.pause(1);
}

export function Validate(endpoint) {
    return endpoint.interface === 1 && endpoint.usage === 0x0001 && endpoint.usage_page === 0xFF00;
}

export function ImageUrl() { return ""; }

/* global forcedColor:readonly, LightingMode:readonly, shutdownColor:readonly */

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)] : [0, 0, 0];
}
