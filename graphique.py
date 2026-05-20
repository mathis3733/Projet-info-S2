from constantes import *
from modele import Piece, King, Queen, Rook, Bishop, Knight, Pawn, Board, Position
from joueurs import Player, AIPlayer, Chess
import math, random, struct

def _make_piece_image(letter, color, size=72):
    fill   = (255, 255, 255) if color == WHITE else (30, 30, 30)
    border = (60, 60, 60)    if color == WHITE else (200, 200, 200)
    if PIL_OK:
        return _pil_piece(letter, color, size, fill, border)
    return _font_piece(letter, color, size, fill, border)

def _pil_piece(letter, color, size, fill, border):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    pad = size // 10; cx = size // 2
    base_h = size // 6
    d.rounded_rectangle([pad, size-base_h-pad//2, size-pad, size-pad//2],
                         radius=4, fill=fill, outline=border, width=2)
    {'K':_dk,'Q':_dq,'R':_dr,'B':_db,'N':_dn,'P':_dp}.get(letter, lambda *_: None)(d, cx, size, pad, fill, border)
    raw  = img.tobytes()
    surf = pygame.image.fromstring(raw, img.size, "RGBA").convert_alpha()
    return surf

def _dk(d,cx,size,pad,fill,border):
    bw=2
    d.rounded_rectangle([cx-size//8,size//4,cx+size//8,size*3//4],radius=3,fill=fill,outline=border,width=bw)
    arm=size//5
    d.rectangle([cx-arm,size//8-size//20,cx+arm,size//8+size//20],fill=border)
    d.rectangle([cx-size//20,size//8-arm//2,cx+size//20,size//8+arm],fill=border)

def _dq(d,cx,size,pad,fill,border):
    bw=2
    d.rounded_rectangle([cx-size//7,size//3,cx+size//7,size*3//4],radius=3,fill=fill,outline=border,width=bw)
    for i,x in enumerate([cx-size//5,cx-size//10,cx,cx+size//10,cx+size//5]):
        r=size//16 if i%2==0 else size//12; y=size//6-r
        d.ellipse([x-r,y-r,x+r,y+r],fill=fill,outline=border,width=bw)

def _dr(d,cx,size,pad,fill,border):
    bw=2; w=size//5
    d.rectangle([cx-w,size//3,cx+w,size*3//4],fill=fill,outline=border,width=bw)
    cw=w*2//3
    for ox in [-w,0,w-cw//2+1]:
        d.rectangle([cx+ox-cw//2,size//5,cx+ox+cw//2,size//3+2],fill=fill,outline=border,width=bw)

def _db(d,cx,size,pad,fill,border):
    bw=2
    points=[(cx,size//8),(cx+size//6,size//2),(cx+size//8,size*3//4),(cx-size//8,size*3//4),(cx-size//6,size//2)]
    d.polygon(points,fill=fill,outline=border)
    r=size//14; d.ellipse([cx-r,size//8-r,cx+r,size//8+r],fill=fill,outline=border,width=bw)

def _dn(d,cx,size,pad,fill,border):
    points=[(cx-size//8,size*3//4),(cx-size//5,size//3),(cx-size//8,size//5),
            (cx+size//12,size//8),(cx+size//5,size//4),(cx+size//6,size//2),(cx+size//8,size*3//4)]
    d.polygon(points,fill=fill,outline=border)
    ex,ey=cx+size//10,size//4; er=size//18
    d.ellipse([ex-er,ey-er,ex+er,ey+er],fill=border)

def _dp(d,cx,size,pad,fill,border):
    bw=2; r=size//6
    d.ellipse([cx-r,size//5,cx+r,size//5+r*2],fill=fill,outline=border,width=bw)
    d.rounded_rectangle([cx-size//10,size//5+r*2-2,cx+size//10,size//2],radius=2,fill=fill,outline=border,width=bw)
    d.rounded_rectangle([cx-size//5,size//2,cx+size//5,size*3//4],radius=3,fill=fill,outline=border,width=bw)

def _font_piece(letter, color, size, fill, border):
    UNICODE = {('K',WHITE):'K',('Q',WHITE):'Q',('R',WHITE):'R',('B',WHITE):'B',('N',WHITE):'N',('P',WHITE):'P',
               ('K',BLACK):'K',('Q',BLACK):'Q',('R',BLACK):'R',('B',BLACK):'B',('N',BLACK):'N',('P',BLACK):'P'}
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    font = pygame.font.SysFont("arial", size - 8, bold=True)
    sym  = UNICODE.get((letter, color), letter)
    col  = (255, 255, 255) if color == WHITE else (20, 20, 20)
    txt  = font.render(sym, True, col)
    surf.blit(txt, ((size - txt.get_width()) // 2, (size - txt.get_height()) // 2))
    return surf



def _build_screamer_sound():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 1, 256)
        sr = 44100; dur = 2.2; n = int(sr * dur); buf = []
        for i in range(n):
            t = i / sr
            v = (math.sin(2*math.pi*80*t)*0.3 + math.sin(2*math.pi*440*t)*0.25
               + math.sin(2*math.pi*1320*t)*0.2 + math.sin(2*math.pi*2200*t)*0.15
               + (random.random()*2-1)*0.1)
            env = min(1.0, i/(sr*0.04))
            if i > n - int(sr*0.15):
                env *= (n - i) / (sr * 0.15)
            buf.append(struct.pack('<h', int(max(-32768, min(32767, v*env*26000)))))
        return pygame.mixer.Sound(buffer=b''.join(buf))
    except Exception:
        return None

def _build_screamer_surface(w, h):
    surf = pygame.Surface((w, h))
    surf.fill((0, 0, 0))
    cx, cy = w // 2, h // 2
    for r in range(min(w, h) // 2, 0, -4):
        c = max(0, min(255, int(80 * (1 - r / (min(w, h) // 2))) * 3))
        try:
            pygame.draw.circle(surf, (c, 0, 0), (cx, cy), r)
        except Exception:
            pass
    face_r = min(w, h) // 3
    pygame.draw.ellipse(surf, (200, 185, 160), (cx-face_r, cy-face_r, face_r*2, face_r*2))
    eye_y = cy - face_r // 4
    for ex in [cx - face_r // 2, cx + face_r // 2]:
        pygame.draw.ellipse(surf, (240, 220, 200), (ex-25, eye_y-18, 50, 38))
        pygame.draw.ellipse(surf, (180, 0, 0),     (ex-14, eye_y-10, 28, 22))
        pygame.draw.ellipse(surf, (0, 0, 0),        (ex-8,  eye_y-6,  16, 14))
        pygame.draw.ellipse(surf, (255, 255, 255),  (ex+2,  eye_y-4,   5,  4))
        for drop in range(3):
            dy = eye_y + 18 + drop * 22
            pygame.draw.line(surf, (160, 0, 0), (ex, eye_y + 18), (ex, dy), 3)
    mouth_y = cy + face_r // 3
    pygame.draw.ellipse(surf, (10, 0, 0), (cx - face_r//2 + 10, mouth_y - 10, face_r - 20, 70))
    for i in range(5):
        tx = cx - 55 + i * 28
        pygame.draw.polygon(surf, (240, 230, 215),
                            [(tx, mouth_y), (tx+22, mouth_y), (tx+11, mouth_y+32)])
    try:
        fnt  = pygame.font.SysFont("arial", 48, bold=True)
        txt  = fnt.render("DERRIERE TOI", True, (220, 0, 0))
        surf.blit(txt, (cx - txt.get_width() // 2, h - 90))
        fnt2 = pygame.font.SysFont("arial", 22)
        txt2 = fnt2.render("(appuie sur une touche...)", True, (140, 0, 0))
        surf.blit(txt2, (cx - txt2.get_width() // 2, h - 40))
    except Exception:
        pass
    return surf



def sq_to_px(ci, ri, flipped=False):
    return (7 - ci if flipped else ci) * SQ, (ri if flipped else 7 - ri) * SQ

def px_to_sq(mx, my, flipped=False):
    ci = mx // SQ; ri = my // SQ
    if flipped: ci = 7 - ci
    else: ri = 7 - ri
    return ci, ri



class Button:

    def __init__(self, x, y, w, h, text, color=None):
        self.rect  = pygame.Rect(x, y, w, h)
        self.text  = text
        self.color = color

    def draw(self, surf, font):
        mx, my = pygame.mouse.get_pos()
        base = self.color if self.color else C_BTN
        col  = tuple(min(255, c + 40) for c in base) if self.rect.collidepoint(mx, my) else base
        pygame.draw.rect(surf, col, self.rect, border_radius=7)
        pygame.draw.rect(surf, C_ACCENT, self.rect, 1, border_radius=7)
        lbl = font.render(self.text, True, C_TEXT)
        surf.blit(lbl, (self.rect.centerx - lbl.get_width() // 2,
                        self.rect.centery - lbl.get_height() // 2))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)



class PieceSkinLoader:

    LETTERS = ['K', 'Q', 'R', 'B', 'N', 'P']
    SIZE    = SQ - 8

    def __init__(self, directory: str = PIECES_DIR):
        self.__directory = directory
        self.__cache: dict = {}

    @property
    def directory(self) -> str:
        return self.__directory

    @directory.setter
    def directory(self, path: str):
        if not isinstance(path, str):
            raise TypeError("directory doit etre une chaine")
        self.__directory = path

    @classmethod
    def from_zip(cls, zip_path: str, extract_to: str = PIECES_DIR) -> 'PieceSkinLoader':
        import zipfile
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Zip introuvable : {zip_path}")
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename.lower().endswith('.png') and basename:
                    target = os.path.join(extract_to, basename)
                    with zf.open(member) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
        return cls(extract_to)

    @staticmethod
    def _candidates(letter: str, color: int, directory: str) -> list:
        c = 'w' if color == WHITE else 'b'
        return [
            os.path.join(directory, f"{letter}{c}.png"),
            os.path.join(directory, f"{c}{letter}.png"),
        ]

    def load_all(self) -> dict:
        self.__cache.clear()
        for color in [WHITE, BLACK]:
            for letter in self.LETTERS:
                surface = self._load_one(letter, color)
                self.__cache[(letter, color)] = surface
        return dict(self.__cache)

    def _load_one(self, letter: str, color: int):
        for path in self._candidates(letter, color, self.__directory):
            if os.path.exists(path):
                try:
                    raw = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(raw, (self.SIZE, self.SIZE))
                except Exception:
                    pass
        return _make_piece_image(letter, color, self.SIZE)

    def apply_single(self, letter: str, color: int, png_path: str) -> bool:
        try:
            raw = pygame.image.load(png_path).convert_alpha()
            img = pygame.transform.smoothscale(raw, (self.SIZE, self.SIZE))
            self.__cache[(letter, color)] = img
            return True
        except Exception:
            return False

    def get(self, letter: str, color: int):
        return self.__cache.get((letter, color))

    def get_all(self) -> dict:
        return dict(self.__cache)

    def clear(self):
        self.__cache.clear()

    def __len__(self):
        return len(self.__cache)

    def __repr__(self):
        return f"PieceSkinLoader(directory='{self.__directory}', loaded={len(self.__cache)})"


