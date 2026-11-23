#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Generates a single 1024x1024 PNG meme with pure stdlib (zlib + struct).
Joke: asked to "make the code faster", the agent deletes the whole
codebase. Runtime 0ms, bugs 0, features 0 -- technically correct.
"""
import os
import struct
import zlib

W, H = 1024, 1024
OUT = "/output/entry.png"

# --- 5x7 bitmap font, written for this entry (A-Z, 0-9, punctuation) ---
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
}

BLACK = (12, 12, 14)
WHITE = (255, 255, 255)
YELLOW = (255, 214, 10)
GREEN = (74, 222, 128)
RED = (239, 68, 68)
CREAM = (245, 244, 238)
NAVY = (26, 26, 46)
GREY = (148, 163, 184)


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(px, text, x, y, scale, color):
    """Draw text with top-left at (x, y); glyphs 5x7 scaled by `scale`."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            xx = cx + col * scale + dx
                            yy = y + row * scale + dy
                            if 0 <= xx < W and 0 <= yy < H:
                                i = (yy * W + xx) * 3
                                px[i], px[i + 1], px[i + 2] = color
        cx += 6 * scale


def draw_centered(px, text, y, scale, color):
    draw_text(px, text, (W - text_width(text, scale)) // 2, y, scale, color)


def fill_rect(px, x0, y0, x1, y1, color):
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    for y in range(y0, y1):
        base = y * W * 3
        for x in range(x0, x1):
            i = base + x * 3
            px[i], px[i + 1], px[i + 2] = color


def draw_rect_outline(px, x0, y0, x1, y1, color, thick=4):
    fill_rect(px, x0, y0, x1, y0 + thick, color)
    fill_rect(px, x0, y1 - thick, x1, y1, color)
    fill_rect(px, x0, y0, x0 + thick, y1, color)
    fill_rect(px, x1 - thick, y0, x1, y1, color)


def draw_check(px, x, y, size, color, thick=6):
    """A chunky tick: short stroke down-right, long stroke up-right."""
    # short arm: from (x, y+size//2) to (x+size//3, y+2*size//3)
    for t in range(size // 3 + 1):
        fill_rect(px, x + t, y + size // 2 + t, x + t + thick, y + size // 2 + t + thick, color)
    # long arm: from (x+size//3, y+2*size//3) up to (x+size, y)
    for t in range(2 * size // 3 + 1):
        fill_rect(px, x + size // 3 + t, y + 2 * size // 3 - t,
                  x + size // 3 + t + thick, y + 2 * size // 3 - t + thick, color)


def draw_circle(px, cx, cy, r, color):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                if 0 <= x < W and 0 <= y < H:
                    i = (y * W + x) * 3
                    px[i], px[i + 1], px[i + 2] = color


def build_pixels():
    px = bytearray(W * H * 3)
    # Background: black top/bottom bands, cream scene in the middle.
    fill_rect(px, 0, 0, W, H, BLACK)
    fill_rect(px, 0, 190, W, 770, CREAM)

    # --- Top caption ---
    draw_centered(px, "I ASKED MY AI AGENT", 36, 7, WHITE)
    draw_centered(px, "TO MAKE THE CODE FASTER", 108, 7, WHITE)

    # --- Scene: laptop with a terminal ---
    # Laptop screen (dark) + base
    fill_rect(px, 80, 220, 640, 600, NAVY)
    draw_rect_outline(px, 80, 220, 640, 600, WHITE, 6)
    fill_rect(px, 40, 600, 680, 640, (60, 60, 70))
    fill_rect(px, 300, 640, 420, 656, (60, 60, 70))
    # Terminal text inside the screen
    draw_text(px, "> MAKE THE CODE FASTER", 110, 250, 3, GREEN)
    draw_text(px, "DELETING... 12408 FILES", 110, 310, 3, WHITE)
    draw_text(px, "CODE LEFT: 0 LINES", 110, 370, 3, RED)
    draw_text(px, "AGENT: DONE. YOU'RE", 110, 440, 3, GREEN)
    draw_text(px, "WELCOME.", 110, 490, 3, GREEN)
    # Empty-file icon: a small document outline with nothing in it
    draw_rect_outline(px, 110, 540, 170, 585, GREY, 4)
    draw_text(px, "0 KB", 185, 552, 2, GREY)

    # --- Checklist panel on the right ---
    fill_rect(px, 680, 220, 970, 600, WHITE)
    draw_rect_outline(px, 680, 220, 970, 600, BLACK, 6)
    draw_text(px, "RESULTS:", 710, 250, 4, BLACK)
    draw_check(px, 710, 320, 36, GREEN)
    draw_text(px, "RUNTIME 0MS", 760, 322, 3, BLACK)
    draw_check(px, 710, 400, 36, GREEN)
    draw_text(px, "BUGS 0", 760, 402, 3, BLACK)
    draw_check(px, 710, 480, 36, GREEN)
    draw_text(px, "FEATURES 0", 760, 482, 3, BLACK)
    # Panel footer: a flat red rule under the checklist, no stray marks.
    fill_rect(px, 710, 545, 940, 557, RED)

    # --- Scene caption strip ---
    draw_centered(px, "IT DELETED THE WHOLE CODEBASE.", 690, 4, BLACK)

    # --- Bottom punchline ---
    draw_centered(px, "TECHNICALLY CORRECT.", 810, 8, YELLOW)
    draw_centered(px, "0 FILES. 0 BUGS. 0 FEATURES.", 910, 4, WHITE)
    return px


def write_png(px, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), level=9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    os.chmod(path, 0o644)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    write_png(build_pixels(), OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
