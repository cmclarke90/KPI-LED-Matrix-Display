# KPI LED Matrix Display

A desk display for glanceable business metrics, built on an Adafruit Matrix Portal S3 and a 32×32 RGB LED matrix. Rotates through four KPI cards every 30 seconds, each with a colored label and large white number. Data is updated via Google Sheets and synced to the display through Zapier and Adafruit IO.

![Hardware: Adafruit Matrix Portal S3 + 32x32 RGB LED Matrix 4mm pitch]

## Hardware

| Component | Details |
|---|---|
| Adafruit Matrix Portal S3 | [Product #5778](https://www.adafruit.com/product/5778) |
| 32×32 RGB LED Matrix (4mm pitch) | [Product #607](https://www.adafruit.com/product/607) |
| 5V 3A USB-C Power Supply | e.g. [Adafruit #4298](https://www.adafruit.com/product/4298) |

The Matrix Portal S3 mounts directly to the back of the panel via the HUB75 connector — no soldering or additional wiring required beyond the power connection.

## Data Pipeline

```
Google Sheets (user edits a cell)
    → Zapier (Paths routing by row, Adafruit IO integration)
    → Adafruit IO (4 feeds under a "portfolio" group)
    → Matrix Portal S3 (polls every 60 minutes)
    → 32×32 LED Matrix
```

## Display Layout

Each KPI gets its own full-screen card:
- **Label** — colored text (Tom Thumb font), centered near top
- **Number** — large white number (LeagueSpartan Bold 16), centered in lower half
- Cards rotate every **30 seconds** with a hard cut between them

### Default KPIs and Colors

| Label | Adafruit IO Feed | Color |
|---|---|---|
| PREDEV | `portfolio.pre-dev` | Yellow |
| CONSTR | `portfolio.cons` | Orange |
| LEASE | `portfolio.lease-up` | Blue |
| STABLE | `portfolio.stab` | Green |

Labels and colors are easily customized in the `CARDS` list at the top of `code.py`.

## Setup

### 1. Adafruit IO

1. Create a free account at [io.adafruit.com](https://io.adafruit.com)
2. Create a Group named `portfolio`
3. Create 4 feeds inside that group: `pre-dev`, `cons`, `lease-up`, `stab`
4. Set each feed to an initial value of `0`
5. Note your **username** and **AIO Key** (under "My Key" in the dashboard)

### 2. Google Sheets

Create a sheet with this structure (tab named `Portfolio`, no header row):

| A | B |
|---|---|
| pre-dev | 0 |
| cons | 0 |
| lease-up | 0 |
| stab | 0 |

Column A is the label (never changes). Column B is the value she edits.

### 3. Zapier

Create a single Zap using **Paths** to route each row to the correct Adafruit IO feed:

- **Trigger:** Google Sheets → "New or Updated Spreadsheet Row", watching column B
- **Path A** (Row 1) → Adafruit IO → Send Data → feed: `portfolio.pre-dev`, value: `{{Value B}}`
- **Path B** (Row 2) → Adafruit IO → Send Data → feed: `portfolio.cons`, value: `{{Value B}}`
- **Path C** (Row 3) → Adafruit IO → Send Data → feed: `portfolio.lease-up`, value: `{{Value B}}`
- **Path D** (Row 4) → Adafruit IO → Send Data → feed: `portfolio.stab`, value: `{{Value B}}`

Connect your Adafruit IO account to Zapier once using your AIO key.

### 4. Device Setup

**Libraries** — copy these from the [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries) into `CIRCUITPY/lib/`:
- `adafruit_requests.mpy`
- `adafruit_connection_manager.mpy`
- `adafruit_display_text/`
- `adafruit_bitmap_font/`

**Fonts** — copy these into `CIRCUITPY/fonts/`:
- `tom-thumb.bdf` — available from [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/fonts/tom-thumb.bdf)
- `LeagueSpartan-Bold-16.bdf` — available from [Adafruit CircuitPython Bitmap Font](https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/tree/main/examples/fonts)

**Credentials** — copy `settings.toml.example` to `settings.toml` and fill in your values:

```toml
CIRCUITPY_WIFI_SSID     = "your-wifi-network-name"
CIRCUITPY_WIFI_PASSWORD = "your-wifi-password"
AIO_USERNAME            = "your-adafruit-io-username"
AIO_KEY                 = "your-adafruit-io-key"
```

**Files** — copy `code.py` and your filled-in `settings.toml` to the root of `CIRCUITPY`.

### 5. Power

Use a **5V 3A USB-C power supply** — a dumb 5V supply, not a USB-PD charger. The official Raspberry Pi USB-C power supply works well. MacBook chargers and Apple USB-C adapters are not recommended as they may negotiate higher voltages or deliver insufficient current.

## File Structure

```
CIRCUITPY/
├── code.py
├── settings.toml          ← not committed, contains credentials
├── lib/
│   ├── adafruit_requests.mpy
│   ├── adafruit_connection_manager.mpy
│   ├── adafruit_display_text/
│   └── adafruit_bitmap_font/
└── fonts/
    ├── tom-thumb.bdf
    └── LeagueSpartan-Bold-16.bdf
```

## Customization

All KPI labels, feed keys, and colors are defined in the `CARDS` list near the top of `code.py`:

```python
CARDS = [
    ("PREDEV",  "portfolio.pre-dev",   (255, 200,   0)),  # yellow
    ("CONSTR",  "portfolio.cons",      (255, 120,   0)),  # orange
    ("LEASE",   "portfolio.lease-up",  ( 80, 140, 255)),  # blue
    ("STABLE",  "portfolio.stab",      ( 60, 200,  80)),  # green
]
```

Rotation interval and fetch interval are also configurable at the top of `code.py`:

```python
REFRESH_SEC = 3600   # how often to fetch from Adafruit IO (seconds)
ROTATE_SEC  = 30     # how long each card is displayed (seconds)
```

## Notes

- The Matrix Portal S3 WiFi is **2.4GHz only** — ensure your network is 2.4GHz WPA2-Personal
- Corporate/enterprise WiFi (WPA2-Enterprise) is not supported by CircuitPython
- A guest network is recommended for office deployments
- `settings.toml` is gitignored — never commit real credentials
