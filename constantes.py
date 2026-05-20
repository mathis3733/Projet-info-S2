import sys, os, json, random, math, struct
from abc import ABC, abstractmethod

try:
    import pygame
    import pygame.gfxdraw
except ImportError:
    print("pygame introuvable. pip install pygame")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import tkinter as tk
    from tkinter import filedialog
    TK_OK = True
except ImportError:
    TK_OK = False


BOARD_PX   = 640
PANEL_W    = 255
WIN_W      = BOARD_PX + PANEL_W
WIN_H      = BOARD_PX
SQ         = BOARD_PX // 8
PIECES_DIR = "pieces"
SAVE_FILE  = "sauvegarde.json"

C_LIGHT   = (240, 217, 181)
C_DARK    = (181, 136,  99)
C_SEL     = ( 50, 200,  50)
C_MOVE    = ( 80, 160, 255)
C_CHECK   = (220,  50,  50)
C_BG      = ( 28,  28,  28)
C_PANEL   = ( 40,  40,  40)
C_TEXT    = (220, 220, 220)
C_ACCENT  = (200, 160,  50)
C_BTN     = ( 70,  70,  70)
C_BTN_HOV = (100, 100, 100)
C_RED_BTN = (160,  30,  30)
C_PURPLE  = (120,  50, 190)

WHITE = 0
BLACK = 1
COLS  = ['a','b','c','d','e','f','g','h']

MODE_CLASSIC   = 'classic'
MODE_CHESS960  = 'chess960'
MODE_CHAOS     = 'chaos'
MODE_ANTICHESS = 'antichess'

SCREAMER_MIN_MS  = 35_000
SCREAMER_MAX_MS  = 120_000
SCREAMER_SHOW_MS = 2_400
PTW_PROCESS_MS   = 3_200


