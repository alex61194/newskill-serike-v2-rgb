# Newskill Serike V2 TKL — RGB Control

Plugin para SignalRGB y scripts Python para controlar la iluminación RGB del teclado **Newskill Serike V2 TKL** (también conocido como "Newski ll Seike v2 TKL").

## Hardware

- **Teclado:** Newskill Serike V2 TKL (86 teclas, formato Tenkeyless)
- **VID/PID:** `0x05AC:0x024F` (hereda ID del Apple Aluminium Keyboard ANSI)
- **Interfaz HID:** Interface 1, Usage Page `0xFF00`, Usage `0x0001` (vendor-defined)
- **Report ID:** `0x06`, tamaño del reporte: 520 bytes

## Protocolo HID (reversado desde USB pcap)

El teclado usa **Feature Reports** HID sobre Interfaz 1. El protocolo tiene 3 pasos:

### 1. INIT (`0x84`)
Inicializa el controlador RGB. Primer reporte que debe enviarse siempre.

```
06 84 00 00 01 00 80 00 + ceros hasta 520 bytes
```

### 2. CONFIG (`0x04`)
Configura los parámetros internos del controlador (modo de color, brillo, etc.).

```
06 04 00 00 01 00 80 00 + 128 bytes de configuración + ceros
```

### 3. APPLY (`0x06`)
Aplica los colores por zonas. Hay **4 zonas** (additivas RGB):
- **Zona 0:** Rojo — offset `0x08`
- **Zona 1:** Verde — offset `0x86` (134)
- **Zona 2:** Azul — offset `0x104` (260)
- **Zona 3:** Offset `0x182` (386, no usado)

Cada zona tiene un **bitmap de 126 bytes** donde `0xFF` = tecla encendida y `0x00` = apagada.
Los colores son **aditivos**: activando zona roja + verde = amarillo.

Cabecera del APPLY:
```
06 06 00 00 01 00 80 01
```

Encabezado + 306 bytes RGB (102 posiciones × 3 canales).

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `Newskill_Serike_V2_TKL.js` | Plugin para **SignalRGB** — mapeo de LEDs, renderizado y envío de colores |
| `newskill_rgb.py` | Script **Python** independiente para controlar RGB desde línea de comandos |

## SignalRGB Plugin

### Instalación
1. Copia `Newskill_Serike_V2_TKL.js` a:
   ```
   %USERPROFILE%\Documents\WhirlwindFX\Plugins\Newskill\
   ```
2. Abre SignalRGB → debería detectar el teclado automáticamente
3. En los ajustes del plugin puedes elegir:
   - **Lighting Mode:** `Canvas` (colores desde SignalRGB) o `Forced` (color fijo)
   - **Forced Color:** color cuando el modo es `Forced`
   - **Shutdown Color:** color al apagar el PC

### Cómo funciona
```javascript
// 102 LEDs mapeados a 86 teclas físicas
var vLeds = [0, 12, 18, ..., 101];
var vLedPositions = [[0,0], [2,0], ..., [17,5]];

// En cada frame (Render):
// 1. Obtiene el color de cada tecla desde SignalRGB
// 2. Construye un array RGB de 306 bytes (102 LEDs × 3)
// 3. Envía el reporte HID de 520 bytes al teclado
// 4. Los LEDs se distribuyen en columnas (0-17) y filas (0-6)

// El layout TKL se define en vLedNames con 86 nombres de teclas
```

### Validación del dispositivo
El plugin solo se activa en el endpoint correcto:
```javascript
endpoint.interface === 1 &&
endpoint.usage === 0x0001 &&
endpoint.usage_page === 0xFF00
```

## Python Script

### Requisitos
```bash
pip install hidapi
```

### Uso
```bash
# Listar dispositivos HID disponibles
python newskill_rgb.py list

# Encender todas las teclas en blanco
python newskill_rgb.py on --vid 0x05ac --pid 0x024f

# Apagar todas las teclas
python newskill_rgb.py off --vid 0x05ac --pid 0x024f

# Colores básicos
python newskill_rgb.py red --vid 0x05ac --pid 0x024f
python newskill_rgb.py green --vid 0x05ac --pid 0x024f
python newskill_rgb.py blue --vid 0x05ac --pid 0x024f

# Test de todos los colores (ciclo de 1.5s cada uno)
python newskill_rgb.py test --vid 0x05ac --pid 0x024f
```

### Cómo funciona
1. Busca el dispositivo HID con VID/PID y sub-device `Col06` + `MI_01`
2. Envía INIT → CONFIG → APPLY en secuencia
3. El APPLY usa 4 zonas de 126 bytes cada una:
   - Zona 0 (Red): bitmap de teclas para canal rojo
   - Zona 1 (Green): bitmap para canal verde
   - Zona 2 (Blue): bitmap para canal azul
4. Solo los 86 bits del TKL bitmap están activos; los demás son `0x00`

## Estructura de teclas (86 teclas TKL)

```
Esc  F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12    Mute
`    1  2  3  4  5  6  7  8  9  0  -  = Bcksp   Ins Home PgUp
Tab  Q  W  E  R  T  Y  U  I  O  P  [  ]  \     Del End  PgDn
Caps A  S  D  F  G  H  J  K  L  ;  '  Enter
LSh  <  Z  X  C  V  B  N  M  ,  .  /  RSh      Up
LCtl Win Alt     Space     Alt Fn Menu RCtl    Left Down Right
```

## Licencia

Este proyecto se proporciona tal cual, fruto de ingeniería inversa sobre USB captures.
