# SPDX-License-Identifier: MIT
"""
Real Estate Portfolio Display
Hardware: Adafruit Matrix Portal S3 + 32x32 RGB LED Matrix (4mm pitch)

Displays 4 portfolio metrics fetched from Adafruit IO feeds.
Rotates through each metric every 30 seconds.
Fetches fresh data from Adafruit IO every 60 minutes.

Feeds (under group "portfolio"):
  portfolio.pre-dev
  portfolio.cons
  portfolio.lease-up
  portfolio.stab

Fonts required (copy to /fonts/ on CIRCUITPY):
  fonts/helvR06.pcf   <- small label font (4x6 pixels)
  fonts/LeagueSpartan-Bold-16.bdf  <- large number font

settings.toml required:
  CIRCUITPY_WIFI_SSID
  CIRCUITPY_WIFI_PASSWORD
  AIO_USERNAME
  AIO_KEY
"""

import os
import ssl
import time
import board
import displayio
import framebufferio
import rgbmatrix
import wifi
import adafruit_connection_manager
import adafruit_requests
import terminalio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# ── Configuration ─────────────────────────────────────────────────────────────

AIO_USERNAME  = os.getenv("AIO_USERNAME")
AIO_KEY       = os.getenv("AIO_KEY")
REFRESH_SEC   = 3600   # fetch new data every 60 minutes
ROTATE_SEC    = 15     # seconds per card

# ── Card definitions ──────────────────────────────────────────────────────────
# Each card: (display label, feed key, label color as RGB tuple)

CARDS = [
    ("PRE DEV",  "portfolio.pre-dev",   (238, 220,   91)),  # yellow
    ("CONS",  "portfolio.cons",      (139, 64,   0)),  # orange
    ("LEASE UP",   "portfolio.lease-up",  ( 48, 92, 222)),  # blue
    ("STAB",  "portfolio.stab",      ( 0, 128, 0)),  # green
]

WHITE  = (255, 255, 255)
DIM    = (51, 51, 51)

# ── Display setup ─────────────────────────────────────────────────────────────

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=32, height=32, bit_depth=4,
    rgb_pins=[
        board.MTX_R1, board.MTX_G1, board.MTX_B1,
        board.MTX_R2, board.MTX_G2, board.MTX_B2,
    ],
    addr_pins=[board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)

display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)
display.brightness = 0.05

# ── Fonts ─────────────────────────────────────────────────────────────────────

try:
    label_font = bitmap_font.load_font("fonts/tom-thumb.bdf")
except Exception:
    label_font = terminalio.FONT   # fallback if font file missing

try:
    number_font = bitmap_font.load_font("fonts/LeagueSpartan-Bold-16.bdf")
except Exception:
    number_font = terminalio.FONT  # fallback

# ── Networking ────────────────────────────────────────────────────────────────

def connect_wifi():
    ssid     = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    print(f"Connecting to {ssid}...")
    wifi.radio.connect(ssid, password)
    print(f"Connected: {wifi.radio.ipv4_address}")

def fetch_feeds():
    """
    Fetch latest value for all 4 feeds from Adafruit IO HTTP API.
    Returns a dict of {feed_key: int_value} or None on failure.
    """
    pool     = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
    ssl_ctx  = ssl.create_default_context()
    requests = adafruit_requests.Session(pool, ssl_ctx)
    headers  = {"X-AIO-Key": AIO_KEY}
    values   = {}

    for _, feed_key, _ in CARDS:
        url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed_key}/data/last"
        try:
            print(f"  Fetching {feed_key}...")
            r    = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            r.close()
            values[feed_key] = int(float(data["value"]))
            print(f"    -> {values[feed_key]}")
        except Exception as e:
            print(f"    Error fetching {feed_key}: {e}")
            values[feed_key] = None

    return values

# ── Display rendering ─────────────────────────────────────────────────────────

def make_card(card_label, value, label_color):
    """
    Build a displayio Group for one portfolio card.
    Layout:
      - Label text, colored, centered near top
      - Large number, white/DIM, centered in lower portion
    """
    group = displayio.Group()

    # ── Label ──────────────────────────────────────────────────────────────
    lbl = label.Label(
        font=label_font,
        text=card_label,
        color=label_color,
        anchor_point=(0.5, 0.0),
        anchored_position=(16, 3),   # centered horizontally, 3px from top
    )
    group.append(lbl)

    # ── Number ─────────────────────────────────────────────────────────────
    display_value = str(value) if value is not None else "--"
    num = label.Label(
        font=number_font,
        text=display_value,
        color=DIM,
        anchor_point=(0.5, 0.5),
        anchored_position=(16, 22),  # centered horizontally, lower half
    )
    group.append(num)

    return group

def show_card(card_label, value, label_color):
    group = make_card(card_label, value, label_color)
    display.root_group = group

def show_blank():
    group = displayio.Group()
    display.root_group = group

# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 40)
    print("  Real Estate Portfolio Display")
    print(f"  Rotate : every {ROTATE_SEC}s")
    print(f"  Refresh: every {REFRESH_SEC // 60}min")
    print("=" * 40)

    connect_wifi()

    feed_data    = None
    last_fetch   = 0
    card_index   = 0
    last_rotate  = 0

    while True:
        now = time.monotonic()

        # ── Fetch data if due ───────────────────────────────────────────────
        if feed_data is None or (now - last_fetch) >= REFRESH_SEC:
            print(f"\nFetching Adafruit IO data...")
            try:
                feed_data  = fetch_feeds()
                last_fetch = now
            except Exception as e:
                print(f"Fetch failed: {e}")
                if feed_data is None:
                    # No data at all yet — show error card and retry in 60s
                    show_card("ERROR", None, (255, 0, 0))
                    time.sleep(60)
                    continue
                # Otherwise keep showing last known data

        # ── Rotate card if due ──────────────────────────────────────────────
        if (now - last_rotate) >= ROTATE_SEC:
            card_label, feed_key, label_color = CARDS[card_index]
            value = feed_data.get(feed_key) if feed_data else None

            print(f"Showing: {card_label} = {value}")
            show_card(card_label, value, label_color)

            card_index  = (card_index + 1) % len(CARDS)
            last_rotate = now

        time.sleep(0.1)


if __name__ == "__main__":
    main()
