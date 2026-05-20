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


class SerializableMixin:

    def to_dict(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict):
        raise NotImplementedError

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str):
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return cls.from_dict(json.load(f))


class Position:

    def __init__(self, column: str, row: int):
        self.__column = column.lower()
        self.__row    = int(row)

    @property
    def column(self) -> str:
        return self.__column

    @property
    def row(self) -> int:
        return self.__row

    def col_index(self) -> int:
        return COLS.index(self.__column)

    def is_valid(self) -> bool:
        return self.__column in COLS and 1 <= self.__row <= 8

    @classmethod
    def from_string(cls, s: str) -> 'Position':
        s = s.strip()
        if len(s) != 2:
            raise ValueError(f"Position invalide : '{s}'")
        col, row = s[0].lower(), s[1]
        if col not in COLS:
            raise ValueError(f"Colonne invalide : '{col}'")
        if not row.isdigit() or not (1 <= int(row) <= 8):
            raise ValueError(f"Ligne invalide : '{row}'")
        return cls(col, int(row))

    @classmethod
    def from_idx(cls, ci: int, ri: int) -> 'Position':
        return cls(COLS[ci], ri + 1)

    @staticmethod
    def are_aligned(p1: 'Position', p2: 'Position') -> bool:
        dc = p1.col_index() - p2.col_index()
        dr = p1.row - p2.row
        return dc == 0 or dr == 0 or abs(dc) == abs(dr)

    def __eq__(self, o):
        return isinstance(o, Position) and self.__column == o.__column and self.__row == o.__row

    def __hash__(self):
        return hash((self.__column, self.__row))

    def __str__(self):
        return f"{self.__column}{self.__row}"

    def __repr__(self):
        return f"Position('{self.__column}', {self.__row})"


class Piece(ABC):

    def __init__(self, position: Position, color: int):
        self.__position = position
        self.__color    = color

    @property
    def position(self) -> Position:
        return self.__position

    @position.setter
    def position(self, p: Position):
        if not isinstance(p, Position):
            raise TypeError("position doit etre une instance de Position")
        self.__position = p

    @property
    def color(self) -> int:
        return self.__color

    def color_name(self) -> str:
        return "Blanc" if self.__color == WHITE else "Noir"

    def _ok_dest(self, pos: Position, board) -> bool:
        t = board.get_piece(pos)
        return t is None or t.color != self.__color

    @staticmethod
    def _path_clear(start: Position, end: Position, board) -> bool:
        dc = end.col_index() - start.col_index()
        dr = end.row - start.row
        sc = (1 if dc > 0 else -1) if dc != 0 else 0
        sr = (1 if dr > 0 else -1) if dr != 0 else 0
        ci, ri = start.col_index() + sc, start.row + sr
        while (ci, ri) != (end.col_index(), end.row):
            if board.get_piece(Position(COLS[ci], ri)) is not None:
                return False
            ci += sc
            ri += sr
        return True

    @abstractmethod
    def isValidMove(self, newPos: Position, board) -> bool: ...

    @abstractmethod
    def __str__(self) -> str: ...

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__position}, {'W' if self.__color == WHITE else 'B'})"


class King(Piece):

    def __init__(self, position: Position, color: int):
        super().__init__(position, color)
        self._has_moved = False

    @property
    def has_moved(self) -> bool:
        return self._has_moved

    @has_moved.setter
    def has_moved(self, v: bool):
        self._has_moved = bool(v)

    def isValidMove(self, p: Position, board) -> bool:
        dc = abs(p.col_index() - self.position.col_index())
        dr = abs(p.row - self.position.row)
        if max(dc, dr) == 1 and self._ok_dest(p, board):
            return True
        if not self._has_moved and dr == 0 and dc == 2:
            return self._can_castle(p, board)
        return False

    def _can_castle(self, p: Position, board) -> bool:
        row  = self.position.row
        kci  = self.position.col_index()
        side = 1 if p.col_index() > kci else -1
        rook_ci = 7 if side == 1 else 0
        rook = board.get_piece(Position(COLS[rook_ci], row))
        if not isinstance(rook, Rook) or rook.has_moved:
            return False
        ci = kci + side
        while ci != rook_ci:
            if board.get_piece(Position(COLS[ci], row)) is not None:
                return False
            ci += side
        opp = BLACK if self.color == WHITE else WHITE
        for ci in [kci, kci + side, kci + 2 * side]:
            pos = Position(COLS[ci], row)
            if any(pc.isValidMove(pos, board) for pc in board.all_pieces(opp)):
                return False
        return True

    def __str__(self): return 'K'


class Queen(Piece):

    def isValidMove(self, p: Position, board) -> bool:
        dc = p.col_index() - self.position.col_index()
        dr = p.row - self.position.row
        if dc == 0 and dr == 0: return False
        if not (dc == 0 or dr == 0 or abs(dc) == abs(dr)): return False
        return self._path_clear(self.position, p, board) and self._ok_dest(p, board)

    def __str__(self): return 'Q'


class Bishop(Piece):

    def isValidMove(self, p: Position, board) -> bool:
        dc = p.col_index() - self.position.col_index()
        dr = p.row - self.position.row
        if dc == 0 and dr == 0: return False
        if abs(dc) != abs(dr): return False
        return self._path_clear(self.position, p, board) and self._ok_dest(p, board)

    def __str__(self): return 'B'


class Knight(Piece):

    def isValidMove(self, p: Position, board) -> bool:
        dc = abs(p.col_index() - self.position.col_index())
        dr = abs(p.row - self.position.row)
        return ((dc == 2 and dr == 1) or (dc == 1 and dr == 2)) and self._ok_dest(p, board)

    def __str__(self): return 'N'


class Rook(Piece):

    def __init__(self, position: Position, color: int):
        super().__init__(position, color)
        self._has_moved = False

    @property
    def has_moved(self) -> bool: return self._has_moved

    @has_moved.setter
    def has_moved(self, v: bool): self._has_moved = bool(v)

    def isValidMove(self, p: Position, board) -> bool:
        dc = p.col_index() - self.position.col_index()
        dr = p.row - self.position.row
        if dc == 0 and dr == 0: return False
        if dc != 0 and dr != 0: return False
        return self._path_clear(self.position, p, board) and self._ok_dest(p, board)

    def __str__(self): return 'R'


class Pawn(Piece):

    def isValidMove(self, p: Position, board) -> bool:
        dc    = p.col_index() - self.position.col_index()
        dr    = p.row - self.position.row
        fwd   = 1 if self.color == WHITE else -1
        start = 2 if self.color == WHITE else 7
        if dc == 0 and dr == fwd:
            return board.get_piece(p) is None
        if dc == 0 and dr == 2 * fwd and self.position.row == start:
            inter = Position(self.position.column, self.position.row + fwd)
            return board.get_piece(inter) is None and board.get_piece(p) is None
        if abs(dc) == 1 and dr == fwd:
            t = board.get_piece(p)
            if t is not None and t.color != self.color:
                return True
            if board.en_passant_target == p:
                return True
        return False

    def __str__(self): return 'P'


PIECE_MAP = {'K': King, 'Q': Queen, 'B': Bishop, 'N': Knight, 'R': Rook, 'P': Pawn}


class Board(SerializableMixin):

    _NB_COLONNES: int = 8

    def __init__(self, mode: str = MODE_CLASSIC):
        self.__grid:   dict = {}
        self.__pieces: dict = {}
        self.__en_passant_target = None
        self.__mode = mode
        self._init()

    @property
    def en_passant_target(self):
        return self.__en_passant_target

    @en_passant_target.setter
    def en_passant_target(self, pos):
        if pos is not None and not isinstance(pos, Position):
            raise TypeError("en_passant_target doit etre une Position ou None")
        self.__en_passant_target = pos

    @property
    def mode(self) -> str:
        return self.__mode

    @classmethod
    def nb_colonnes(cls) -> int:
        return cls._NB_COLONNES

    def _init(self):
        self.__grid.clear()
        self.__pieces.clear()
        self.__en_passant_target = None
        if self.__mode == MODE_CHAOS:
            self._chaos_init()
            return
        for col in COLS:
            self._place(Pawn(Position(col, 2), WHITE))
            self._place(Pawn(Position(col, 7), BLACK))
        back = self._chess960_row() if self.__mode == MODE_CHESS960 \
               else [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i, cls in enumerate(back):
            self._place(cls(Position(COLS[i], 1), WHITE))
            self._place(cls(Position(COLS[i], 8), BLACK))

    @staticmethod
    def _chess960_row() -> list:
        while True:
            row = [None] * 8
            light = random.choice([0, 2, 4, 6]); row[light] = Bishop
            dark  = random.choice([1, 3, 5, 7]); row[dark]  = Bishop
            empty = [i for i in range(8) if row[i] is None]
            qi = random.choice(empty); row[qi] = Queen; empty.remove(qi)
            n1 = random.choice(empty); row[n1] = Knight; empty.remove(n1)
            n2 = random.choice(empty); row[n2] = Knight; empty.remove(n2)
            row[empty[0]] = Rook; row[empty[1]] = King; row[empty[2]] = Rook
            if all(r is not None for r in row): return row

    def _chaos_init(self):
        all_sq = [(c, r) for c in range(8) for r in range(1, 9)]
        random.shuffle(all_sq)
        pieces = [King, Queen, Rook, Rook, Bishop, Bishop, Knight, Knight] + [Pawn] * 8
        combined = [(cls, WHITE) for cls in pieces] + [(cls, BLACK) for cls in pieces]
        for i, (cls, color) in enumerate(combined):
            pos = Position(COLS[all_sq[i][0]], all_sq[i][1])
            self._place(cls(pos, color))

    def _place(self, piece: Piece):
        self.__grid[piece.position]  = piece
        self.__pieces[id(piece)]     = piece

    def get_piece(self, pos: Position):
        return self.__grid.get(pos)

    def all_pieces(self, color=None) -> list:
        ps = list(self.__pieces.values())
        return [p for p in ps if p.color == color] if color is not None else ps

    def find_king(self, color: int):
        for p in self.__pieces.values():
            if isinstance(p, King) and p.color == color:
                return p
        return None

    def is_in_check(self, color: int) -> bool:
        king = self.find_king(color)
        if not king: return False
        opp = BLACK if color == WHITE else WHITE
        return any(p.isValidMove(king.position, self) for p in self.all_pieces(opp))

    def promote_pawn(self, pawn: Pawn, new_cls) -> Piece:
        pos = pawn.position
        del self.__grid[pos]
        del self.__pieces[id(pawn)]
        new_piece = new_cls(pos, pawn.color)
        self._place(new_piece)
        return new_piece

    def _sim_remove(self, pos: Position):
        piece = self.__grid.pop(pos, None)
        if piece:
            self.__pieces.pop(id(piece), None)
        return piece

    def _sim_restore(self, piece: Piece, pos: Position):
        piece.position = pos
        self.__grid[pos]         = piece
        self.__pieces[id(piece)] = piece

    def move_piece(self, piece: Piece, new_pos: Position, is_simulation: bool = False):
        prev_ep = self.__en_passant_target
        if not is_simulation:
            self.__en_passant_target = None
        target = self.__grid.get(new_pos)
        if target:
            del self.__pieces[id(target)]
        if isinstance(piece, Pawn) and prev_ep == new_pos and not is_simulation:
            fwd = 1 if piece.color == WHITE else -1
            ep_pos  = Position(new_pos.column, new_pos.row - fwd)
            ep_pawn = self.__grid.get(ep_pos)
            if ep_pawn:
                del self.__pieces[id(ep_pawn)]
                del self.__grid[ep_pos]
        if isinstance(piece, King) and not is_simulation:
            dc = new_pos.col_index() - piece.position.col_index()
            if abs(dc) == 2:
                row  = piece.position.row
                side = 1 if dc > 0 else -1
                rook = self.__grid.get(Position('h' if side == 1 else 'a', row))
                rook_dest = Position('f' if side == 1 else 'd', row)
                if rook:
                    del self.__grid[rook.position]
                    rook.position = rook_dest
                    self.__grid[rook_dest] = rook
                    rook.has_moved = True
        del self.__grid[piece.position]
        piece.position = new_pos
        self.__grid[new_pos] = piece
        if not is_simulation:
            if hasattr(piece, 'has_moved'):
                piece.has_moved = True
            if isinstance(piece, Pawn):
                fwd   = 1 if piece.color == WHITE else -1
                start = 2 if piece.color == WHITE else 7
                orig_row = new_pos.row - 2 * fwd
                if orig_row == start:
                    self.__en_passant_target = Position(new_pos.column, new_pos.row - fwd)

    def to_dict(self) -> dict:
        TYPE = {King:'King', Queen:'Queen', Bishop:'Bishop',
                Knight:'Knight', Rook:'Rook', Pawn:'Pawn'}
        pieces = []
        for p in self.__pieces.values():
            d = {'type': TYPE[type(p)], 'color': p.color,
                 'col': p.position.column, 'row': p.position.row}
            if hasattr(p, 'has_moved'):
                d['has_moved'] = p.has_moved
            pieces.append(d)
        ep = str(self.__en_passant_target) if self.__en_passant_target else None
        return {'pieces': pieces, 'en_passant': ep, 'mode': self.__mode}

    @classmethod
    def from_dict(cls, data: dict) -> 'Board':
        TM = {'King': King, 'Queen': Queen, 'Bishop': Bishop,
              'Knight': Knight, 'Rook': Rook, 'Pawn': Pawn}
        b = cls.__new__(cls)
        b._Board__grid    = {}
        b._Board__pieces  = {}
        b._Board__en_passant_target = None
        b._Board__mode    = data.get('mode', MODE_CLASSIC)
        for d in data['pieces']:
            piece = TM[d['type']](Position(d['col'], d['row']), d['color'])
            if 'has_moved' in d and hasattr(piece, 'has_moved'):
                piece.has_moved = d['has_moved']
            b._place(piece)
        ep = data.get('en_passant')
        b._Board__en_passant_target = Position.from_string(ep) if ep else None
        return b


class Player:

    def __init__(self, name: str, color: int):
        self.__name  = name
        self.__color = color

    @property
    def name(self) -> str:
        return self.__name

    @property
    def color(self) -> int:
        return self.__color

    def color_name(self) -> str:
        return "Blanc" if self.__color == WHITE else "Noir"

    def is_ai(self) -> bool:
        return False

    def __str__(self):
        return f"{self.__name} ({self.color_name()})"

    def __repr__(self):
        return f"Player('{self.__name}', {self.__color})"


class AIPlayer(Player):

    def __init__(self, color: int):
        super().__init__("IA", color)
        self._board = None
        self._chess = None

    def is_ai(self) -> bool:
        return True

    def set_board(self, board: Board, chess=None):
        self._board = board
        self._chess = chess

    def get_move(self):
        if not self._board or not self._chess:
            return None
        moves = [(p, d) for p in self._board.all_pieces(self.color)
                         for d in self._chess.legal_destinations(p)]
        if not moves:
            return None
        captures = [(p, d) for p, d in moves if self._board.get_piece(d) is not None]
        if self._chess.mode == MODE_ANTICHESS and captures:
            return random.choice(captures)
        return random.choice(captures) if captures else random.choice(moves)


class Chess(SerializableMixin):

    def __init__(self, mode: str = MODE_CLASSIC):
        self.__mode    = mode
        self.board     = Board(mode=mode)
        self.players: list = []
        self.__current = None
        self.__history: list = []

    @property
    def mode(self) -> str:
        return self.__mode

    @property
    def currentPlayer(self):
        return self.__current

    @currentPlayer.setter
    def currentPlayer(self, p):
        if p is not None and not isinstance(p, Player):
            raise TypeError("currentPlayer doit etre une instance de Player")
        self.__current = p

    @property
    def _history(self):
        return self.__history

    def apply_move_pieces(self, piece: Piece, dest: Position, promotion_choice=None):
        orig     = str(piece.position)
        captured = self.board.get_piece(dest)
        self.board.move_piece(piece, dest)
        entry = f"{str(piece)}{orig}>{dest}"
        if captured:
            entry += f"x{str(captured)}"
        promo_row = 8 if piece.color == WHITE else 1
        if isinstance(piece, Pawn) and dest.row == promo_row:
            new_cls = promotion_choice or Queen
            self.board.promote_pawn(piece, new_cls)
            entry += f"={new_cls.__name__[0]}"
        self.__history.append(entry)

    def switchPlayer(self):
        self.currentPlayer = (
            self.players[1] if self.currentPlayer == self.players[0]
            else self.players[0]
        )
        if self.currentPlayer.is_ai():
            self.currentPlayer.set_board(self.board, self)

    def legal_destinations(self, piece: Piece) -> list:
        dests = []
        for ci in range(8):
            for ri in range(8):
                dest = Position.from_idx(ci, ri)
                if dest == piece.position:
                    continue
                if not piece.isValidMove(dest, self.board):
                    continue
                if self.__mode != MODE_ANTICHESS:
                    if self._still_check_after(piece, dest, piece.color):
                        continue
                dests.append(dest)
        return dests

    def _still_check_after(self, piece: Piece, dest: Position, color: int) -> bool:
        board    = self.board
        orig     = piece.position
        prev_ep  = board.en_passant_target
        captured = board._sim_remove(dest)
        board.move_piece(piece, dest, is_simulation=True)
        result = board.is_in_check(color)
        board._sim_remove(dest)
        board._sim_restore(piece, orig)
        if captured:
            board._sim_restore(captured, dest)
        board.en_passant_target = prev_ep
        return result

    def has_legal_moves(self, color: int) -> bool:
        return any(self.legal_destinations(p) for p in self.board.all_pieces(color))

    def to_dict(self) -> dict:
        return {
            'board':         self.board.to_dict(),
            'players':       [{'name': p.name, 'color': p.color, 'is_ai': p.is_ai()}
                               for p in self.players],
            'current_color': self.currentPlayer.color if self.currentPlayer else None,
            'history':       self.__history,
            'mode':          self.__mode,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Chess':
        chess = cls.__new__(cls)
        chess._Chess__mode    = data.get('mode', MODE_CLASSIC)
        chess.board           = Board.from_dict(data['board'])
        chess._Chess__history = data.get('history', [])
        chess.players = []
        for pd in data['players']:
            if pd['is_ai']:
                p = AIPlayer(pd['color'])
                p.set_board(chess.board, chess)
            else:
                p = Player(pd['name'], pd['color'])
            chess.players.append(p)
        cur_color = data.get('current_color')
        chess._Chess__current = next(
            (p for p in chess.players if p.color == cur_color), None
        )
        return chess

    def save(self, path: str = SAVE_FILE):
        super().save(path)

    @classmethod
    def load_from_file(cls, path: str = SAVE_FILE):
        return cls.load(path)


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


class ChessApp:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Jeu d'Echecs - Projet I1")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        try:
            pygame.display.set_icon(_make_piece_image('K', WHITE, 32))
        except Exception:
            pass
        self.clock = pygame.time.Clock()

        self.fnt_lbl   = pygame.font.SysFont("arial,helvetica", 14)
        self.fnt_panel = pygame.font.SysFont("arial,helvetica", 13)
        self.fnt_title = pygame.font.SysFont("arial,helvetica", 17, bold=True)
        self.fnt_big   = pygame.font.SysFont("arial,helvetica", 36, bold=True)
        self.fnt_coord = pygame.font.SysFont("arial,helvetica", 11)
        self.fnt_small = pygame.font.SysFont("arial,helvetica", 12)

        self._skin_loader = PieceSkinLoader(PIECES_DIR)
        self._piece_imgs: dict = {}
        self._load_piece_images()

        px = BOARD_PX + 8; bw = PANEL_W - 16; bh = 30
        self.btn_save = Button(px, WIN_H - 175, bw, bh, "Sauvegarder  (S)")
        self.btn_load = Button(px, WIN_H - 138, bw, bh, "Charger  (L)")
        self.btn_flip = Button(px, WIN_H - 101, bw, bh, "Retourner  (F)")
        self.btn_skin = Button(px, WIN_H -  64, bw, bh, "Importer Skin", C_PURPLE)
        self.btn_ptw  = Button(px, WIN_H -  27, bw, bh, "PAY TO WIN", C_RED_BTN)

        self.selected:    Piece = None
        self.legal_dests: list  = []
        self.message     = ""
        self.msg_color   = C_TEXT
        self.flipped     = False
        self.game_over   = False
        self.winner_name = ""
        self.ai_delay    = 0
        self.state       = "menu"

        self.screamer_sound   = _build_screamer_sound()
        self.screamer_surface = None
        self.screamer_active  = False
        self.screamer_until   = 0
        self._reset_screamer_timer()

        self.ptw_active = False
        self.ptw_amount = ""
        self.ptw_phase  = "input"
        self.ptw_start  = 0

        self.chess = Chess()

    def _reset_screamer_timer(self):
        self.screamer_next = pygame.time.get_ticks() + random.randint(SCREAMER_MIN_MS, SCREAMER_MAX_MS)

    def _load_piece_images(self):
        self._piece_imgs = self._skin_loader.load_all()

    def reload_piece_images(self):
        self._skin_loader.clear()
        self._piece_imgs = self._skin_loader.load_all()
        self._set_msg("Images rechargees.", C_ACCENT)

    def load_skin_from_zip(self, zip_path: str):
        try:
            self._skin_loader = PieceSkinLoader.from_zip(zip_path, PIECES_DIR)
            self._piece_imgs  = self._skin_loader.load_all()
            self._set_msg(f"Skin charge depuis {os.path.basename(zip_path)}", C_ACCENT)
        except Exception as e:
            self._set_msg(f"Erreur zip : {e}", C_CHECK)

    def _skin_dialog(self):
        choice = self._popup_choose("Source du skin", ['Fichier PNG', 'Dossier ZIP'])
        if choice is None: return

        if choice == 'Dossier ZIP':
            if not TK_OK:
                self._set_msg("tkinter introuvable.", C_CHECK); return
            root = tk.Tk(); root.withdraw()
            zip_path = filedialog.askopenfilename(title="Selectionner un ZIP",
                                                  filetypes=[("ZIP", "*.zip"), ("Tous", "*.*")])
            root.destroy()
            if not zip_path: self._set_msg("Annule.", C_TEXT); return
            self.load_skin_from_zip(zip_path)
            return

        letter  = self._popup_choose("Choisir la piece", ['K', 'Q', 'R', 'B', 'N', 'P'])
        if letter is None: return
        color_s = self._popup_choose("Couleur cible", ['Blancs', 'Noirs', 'Les deux'])
        if color_s is None: return
        if not TK_OK:
            self._set_msg("tkinter introuvable.", C_CHECK); return
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename(title="Selectionner un PNG",
                                          filetypes=[("PNG", "*.png"), ("Tous", "*.*")])
        root.destroy()
        if not path:
            self._set_msg("Annule.", C_TEXT); return
        colors = {'Blancs': [WHITE], 'Noirs': [BLACK], 'Les deux': [WHITE, BLACK]}.get(color_s, [])
        ok = False
        for col in colors:
            if self._skin_loader.apply_single(letter, col, path):
                self._piece_imgs[(letter, col)] = self._skin_loader.get(letter, col)
                ok = True
        self._set_msg(f"Skin applique a {letter}." if ok else "Echec chargement.", C_ACCENT if ok else C_CHECK)

    def _popup_choose(self, title, options):
        bw = 110; bh = 44; gap = 10
        total_w = len(options) * (bw + gap) - gap
        ox = WIN_W // 2 - total_w // 2
        oy = WIN_H // 2 - bh // 2
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for i, opt in enumerate(options):
                        bx = ox + i * (bw + gap)
                        if bx < mx < bx + bw and oy < my < oy + bh: return opt
            ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 180))
            self.screen.blit(ov, (0, 0))
            t = self.fnt_title.render(title, True, C_ACCENT)
            self.screen.blit(t, (WIN_W // 2 - t.get_width() // 2, oy - 50))
            mx_c, my_c = pygame.mouse.get_pos()
            for i, opt in enumerate(options):
                bx = ox + i * (bw + gap)
                hov = bx < mx_c < bx + bw and oy < my_c < oy + bh
                pygame.draw.rect(self.screen, C_ACCENT if hov else C_BTN,
                                 (bx, oy, bw, bh), border_radius=8)
                lbl = self.fnt_panel.render(opt, True, (20, 20, 20) if hov else C_TEXT)
                self.screen.blit(lbl, (bx + bw // 2 - lbl.get_width() // 2,
                                       oy + bh // 2 - lbl.get_height() // 2))
            pygame.display.flip()
            self.clock.tick(60)

    def _pay_to_win_open(self):
        self.ptw_active = True
        self.ptw_amount = ""
        self.ptw_phase  = "input"

    def _pay_to_win_draw(self):
        now = pygame.time.get_ticks()
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))
        bw, bh = 460, 260
        bx, by = WIN_W // 2 - bw // 2, WIN_H // 2 - bh // 2
        cx = bx + bw // 2
        pygame.draw.rect(self.screen, (30, 25, 10),   (bx, by, bw, bh), border_radius=14)
        pygame.draw.rect(self.screen, (200, 160, 50), (bx, by, bw, bh), 2, border_radius=14)

        if self.ptw_phase == "input":
            t1 = self.fnt_big.render("PAY TO WIN", True, (220, 180, 30))
            self.screen.blit(t1, (cx - t1.get_width() // 2, by + 18))
            t2 = self.fnt_panel.render("Entrez le montant a envoyer :", True, C_TEXT)
            self.screen.blit(t2, (cx - t2.get_width() // 2, by + 75))
            fr = pygame.Rect(bx + 80, by + 100, bw - 160, 40)
            pygame.draw.rect(self.screen, (50, 45, 20), fr, border_radius=6)
            pygame.draw.rect(self.screen, C_ACCENT, fr, 2, border_radius=6)
            cur = "|" if pygame.time.get_ticks() % 800 < 400 else ""
            amt = self.fnt_lbl.render(self.ptw_amount + cur, True, (255, 220, 80))
            self.screen.blit(amt, (fr.x + 10, fr.y + 10))
            btn = pygame.Rect(cx - 80, by + bh - 55, 160, 38)
            mx, my = pygame.mouse.get_pos()
            hov = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (180, 130, 20) if hov else (120, 90, 10),
                             btn, border_radius=8)
            bl = self.fnt_title.render("ENVOYER", True, (20, 15, 0))
            self.screen.blit(bl, (btn.centerx - bl.get_width() // 2,
                                  btn.centery - bl.get_height() // 2))
            esc = self.fnt_coord.render("[Echap] Annuler", True, (100, 100, 100))
            self.screen.blit(esc, (cx - esc.get_width() // 2, by + bh - 12))

        elif self.ptw_phase == "processing":
            elapsed  = now - self.ptw_start
            progress = min(1.0, elapsed / PTW_PROCESS_MS)
            t1 = self.fnt_title.render("Paiement en cours...", True, C_ACCENT)
            self.screen.blit(t1, (cx - t1.get_width() // 2, by + 40))
            t2 = self.fnt_panel.render(f"Montant : {self.ptw_amount} EUR", True, (200, 200, 200))
            self.screen.blit(t2, (cx - t2.get_width() // 2, by + 80))
            bar = pygame.Rect(bx + 60, by + 115, bw - 120, 22)
            pygame.draw.rect(self.screen, (50, 50, 50), bar, border_radius=8)
            fw = int((bw - 120) * progress)
            if fw > 0:
                pygame.draw.rect(self.screen, (80, 180, 60),
                                 (bar.x, bar.y, fw, 22), border_radius=8)
            pygame.draw.rect(self.screen, C_ACCENT, bar, 1, border_radius=8)
            steps = ["Connexion au serveur...", "Verification bancaire...",
                     "Contournement du firewall...", "Corruption du plateau..."]
            si = min(3, int(progress * 4))
            for i, msg in enumerate(steps[:si + 1]):
                col = (80, 200, 80) if i < si else C_ACCENT
                s   = self.fnt_small.render(f"  {'v' if i < si else '>'}  {msg}", True, col)
                self.screen.blit(s, (bx + 60, by + 150 + i * 20))
            if elapsed >= PTW_PROCESS_MS:
                self.ptw_phase = "done"

        elif self.ptw_phase == "done":
            t1 = self.fnt_big.render("PAIEMENT ACCEPTE", True, (80, 220, 80))
            self.screen.blit(t1, (cx - t1.get_width() // 2, by + 30))
            t2 = self.fnt_title.render(f"{self.chess.currentPlayer.name} a gagne !", True, C_ACCENT)
            self.screen.blit(t2, (cx - t2.get_width() // 2, by + 90))
            t3 = self.fnt_panel.render(f"Transaction de {self.ptw_amount} EUR confirmee.", True, C_TEXT)
            self.screen.blit(t3, (cx - t3.get_width() // 2, by + 125))
            t4 = self.fnt_coord.render("(cliquez ou Entree pour continuer)", True, (100, 100, 100))
            self.screen.blit(t4, (cx - t4.get_width() // 2, by + bh - 25))

    def _pay_to_win_handle(self, event):
        if event.type == pygame.KEYDOWN:
            if self.ptw_phase == "input":
                if event.key == pygame.K_ESCAPE:
                    self.ptw_active = False
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.ptw_amount.strip():
                        self.ptw_phase = "processing"
                        self.ptw_start = pygame.time.get_ticks()
                elif event.key == pygame.K_BACKSPACE:
                    self.ptw_amount = self.ptw_amount[:-1]
                elif event.unicode and len(self.ptw_amount) < 20:
                    self.ptw_amount += event.unicode
            elif self.ptw_phase == "done":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.ptw_active = False
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.ptw_phase == "input":
                bw, bh = 460, 260
                bx = WIN_W // 2 - bw // 2
                by = WIN_H // 2 - bh // 2
                cx = bx + bw // 2
                btn = pygame.Rect(cx - 80, by + bh - 55, 160, 38)
                if btn.collidepoint(event.pos) and self.ptw_amount.strip():
                    self.ptw_phase = "processing"
                    self.ptw_start = pygame.time.get_ticks()
            elif self.ptw_phase == "done":
                self.ptw_active = False
                return True
        return False

    def _trigger_screamer(self):
        self.screamer_active  = True
        self.screamer_until   = pygame.time.get_ticks() + SCREAMER_SHOW_MS
        self.screamer_surface = _build_screamer_surface(WIN_W, WIN_H)
        if self.screamer_sound:
            try:
                self.screamer_sound.play()
            except Exception:
                pass

    def _set_msg(self, txt, color=C_TEXT):
        self.message = txt
        self.msg_color = color

    def run_menu(self):
        inputs = ["", ""]
        active = 0
        labels = ["Joueur Blanc (ou IA) :", "Joueur Noir (ou IA) :"]
        mode_btns = [
            (MODE_CLASSIC,   'Classique',    (60,  100,  40)),
            (MODE_CHESS960,  'Chess 960',    (100,  60,  20)),
            (MODE_CHAOS,     'Chaos',         (120,  30, 120)),
            (MODE_ANTICHESS, 'Anti-Echecs',  (120,  20,  20)),
        ]
        mode_descs = {
            MODE_CLASSIC:   "Placement standard",
            MODE_CHESS960:  "Pieces melangees",
            MODE_CHAOS:     "Pieces n'importe ou",
            MODE_ANTICHESS: "Perdez toutes vos pieces",
        }
        bw = (WIN_W - 50) // 4 - 5
        bh = 46
        mode_y = WIN_H // 2 + 105

        while self.state == "menu":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if active == 0: active = 1
                        else: self._start_game(inputs); return
                    elif event.key == pygame.K_TAB:
                        active = 1 - active
                    elif event.key == pygame.K_BACKSPACE:
                        inputs[active] = inputs[active][:-1]
                    elif event.unicode and len(inputs[active]) < 18:
                        inputs[active] += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for i in range(2):
                        by_ = WIN_H // 2 - 60 + i * 85
                        if WIN_W // 2 - 160 < mx < WIN_W // 2 + 160 and by_ < my < by_ + 36:
                            active = i
                    for j, (mode, label, col) in enumerate(mode_btns):
                        bx_ = 25 + j * (bw + 5)
                        if bx_ < mx < bx_ + bw and mode_y < my < mode_y + bh:
                            self._start_game(inputs, mode=mode); return

            self.screen.fill(C_BG)
            t1 = self.fnt_big.render("Jeu d'Echecs", True, C_ACCENT)
            self.screen.blit(t1, (WIN_W // 2 - t1.get_width() // 2, 50))
            t2 = self.fnt_lbl.render("Projet I1 - 2025/2026", True, (130, 130, 130))
            self.screen.blit(t2, (WIN_W // 2 - t2.get_width() // 2, 105))

            for i in range(2):
                by_ = WIN_H // 2 - 60 + i * 85
                col = C_ACCENT if active == i else (80, 80, 80)
                pygame.draw.rect(self.screen, col,
                                 (WIN_W // 2 - 160, by_, 320, 36), 2, border_radius=7)
                lbl = self.fnt_small.render(labels[i], True, (150, 150, 150))
                self.screen.blit(lbl, (WIN_W // 2 - 160, by_ - 18))
                cur = "|" if active == i and pygame.time.get_ticks() % 900 < 450 else ""
                txt = self.fnt_lbl.render(inputs[i] + cur, True, C_TEXT)
                self.screen.blit(txt, (WIN_W // 2 - 148, by_ + 8))

            mx_c, my_c = pygame.mouse.get_pos()
            for j, (mode, label, col) in enumerate(mode_btns):
                bx_ = 25 + j * (bw + 5)
                hov = bx_ < mx_c < bx_ + bw and mode_y < my_c < mode_y + bh
                bg  = tuple(min(255, c + 50) for c in col) if hov else col
                pygame.draw.rect(self.screen, bg, (bx_, mode_y, bw, bh), border_radius=10)
                lbl = self.fnt_title.render(label, True, (230, 230, 230))
                self.screen.blit(lbl, (bx_ + bw // 2 - lbl.get_width() // 2, mode_y + 4))
                desc = self.fnt_coord.render(mode_descs[mode], True, (180, 180, 180))
                self.screen.blit(desc, (bx_ + bw // 2 - desc.get_width() // 2, mode_y + bh - 16))

            hint = self.fnt_coord.render(
                "Skins : placez vos PNG dans ./pieces/  |  [R] pour recharger",
                True, (90, 90, 90))
            self.screen.blit(hint, (WIN_W // 2 - hint.get_width() // 2, WIN_H - 28))
            pygame.display.flip()
            self.clock.tick(60)

    def _start_game(self, inputs, mode=MODE_CLASSIC):
        n0 = inputs[0].strip() or "Joueur 1"
        n1 = inputs[1].strip() or "Joueur 2"
        self.chess = Chess(mode=mode)
        for name, color in [(n0, WHITE), (n1, BLACK)]:
            p = AIPlayer(color) if name.upper() == "IA" else Player(name, color)
            if p.is_ai():
                p.set_board(self.chess.board, self.chess)
            self.chess.players.append(p)
        self.chess.currentPlayer = self.chess.players[0]
        self.state       = "game"
        self.game_over   = False
        self.winner_name = ""
        self.selected    = None
        self.legal_dests = []
        self._reset_screamer_timer()
        suffix = {
            MODE_CHESS960:  " [Chess 960]",
            MODE_CHAOS:     " [Chaos]",
            MODE_ANTICHESS: " [Anti-Echecs]",
        }.get(mode, "")
        self._set_msg(f"A {self.chess.currentPlayer.name} de jouer{suffix}", C_TEXT)

    def run_game(self):
        while self.state == "game":
            dt  = self.clock.tick(60)
            now = pygame.time.get_ticks()
            if not self.screamer_active and not self.game_over and now >= self.screamer_next:
                self._trigger_screamer()
                self._reset_screamer_timer()
            if self.screamer_active and now >= self.screamer_until:
                self.screamer_active = False
            self._handle_events()
            if (self.state == "game" and not self.game_over
                    and not self.ptw_active and not self.screamer_active
                    and self.chess.currentPlayer.is_ai()):
                self.ai_delay += dt
                if self.ai_delay >= 600:
                    self.ai_delay = 0
                    self._ai_play()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if self.screamer_active:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.screamer_active = False
                continue
            if self.ptw_active:
                won = self._pay_to_win_handle(event)
                if won:
                    self._ptw_victory()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: self._save()
                if event.key == pygame.K_l: self._load()
                if event.key == pygame.K_f: self.flipped = not self.flipped
                if event.key == pygame.K_r: self.reload_piece_images()
                if event.key == pygame.K_ESCAPE:
                    self.selected = None; self.legal_dests = []
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                mx, my = event.pos
                if mx < BOARD_PX:
                    self._handle_board_click(mx, my)
                else:
                    if self.btn_save.clicked(event): self._save()
                    if self.btn_load.clicked(event): self._load()
                    if self.btn_flip.clicked(event): self.flipped = not self.flipped
                    if self.btn_skin.clicked(event): self._skin_dialog()
                    if self.btn_ptw.clicked(event):  self._pay_to_win_open()

    def _handle_board_click(self, mx, my):
        ci, ri = px_to_sq(mx, my, self.flipped)
        if not (0 <= ci < 8 and 0 <= ri < 8): return
        clicked_pos   = Position.from_idx(ci, ri)
        clicked_piece = self.chess.board.get_piece(clicked_pos)
        cp = self.chess.currentPlayer

        if self.selected is None:
            if clicked_piece and clicked_piece.color == cp.color:
                self.selected    = clicked_piece
                self.legal_dests = self.chess.legal_destinations(clicked_piece)
                self._set_msg(f"{str(clicked_piece)}{clicked_pos} - {len(self.legal_dests)} coups", C_ACCENT)
        else:
            if clicked_pos in self.legal_dests:
                piece = self.selected
                promo_row = 8 if piece.color == WHITE else 1
                if isinstance(piece, Pawn) and clicked_pos.row == promo_row:
                    self.selected = None; self.legal_dests = []
                    choice = self._promotion_dialog()
                    self.chess.apply_move_pieces(piece, clicked_pos, promotion_choice=choice)
                else:
                    self.chess.apply_move_pieces(piece, clicked_pos)
                self.selected = None; self.legal_dests = []
                self._post_move()
            elif clicked_piece and clicked_piece.color == cp.color:
                self.selected    = clicked_piece
                self.legal_dests = self.chess.legal_destinations(clicked_piece)
                self._set_msg(f"{str(clicked_piece)}{clicked_pos} selectionne", C_ACCENT)
            else:
                self.selected = None; self.legal_dests = []

    def _post_move(self):
        self.chess.switchPlayer()
        cp = self.chess.currentPlayer

        if self.chess.mode == MODE_ANTICHESS:
            for player in self.chess.players:
                if len(self.chess.board.all_pieces(player.color)) == 0:
                    self.winner_name = f"{player.name} ({player.color_name()})"
                    self.game_over   = True
                    self._set_msg("Toutes les pieces perdues ! Victoire !", C_ACCENT)
                    return
            self._set_msg(f"A {cp.name} - perdez vos pieces !", (180, 120, 220))
            return

        self.flipped = (cp.color == BLACK)
        if self.chess.board.find_king(cp.color) is None:
            prev = self.chess.players[1] if cp == self.chess.players[0] else self.chess.players[0]
            self.winner_name = f"{prev.name} ({prev.color_name()})"
            self.game_over   = True
            self._set_msg(f"Roi capture ! {self.winner_name} gagne !", C_CHECK)
            return

        has_moves = self.chess.has_legal_moves(cp.color)
        in_check  = self.chess.board.is_in_check(cp.color)

        if not has_moves:
            if in_check:
                prev = self.chess.players[1] if cp == self.chess.players[0] else self.chess.players[0]
                self.winner_name = f"{prev.name} ({prev.color_name()})"
                self.game_over   = True
                self._set_msg("ECHEC ET MAT !", C_CHECK)
            else:
                self.winner_name = "Personne (Pat)"
                self.game_over   = True
                self._set_msg("PAT - Partie nulle !", C_ACCENT)
        elif in_check:
            self._set_msg(f"ECHEC ! A {cp.name} de jouer.", (255, 180, 0))
        else:
            self._set_msg(f"A {cp.name} de jouer ({cp.color_name()})", C_TEXT)

    def _ptw_victory(self):
        cp = self.chess.currentPlayer
        self.winner_name = f"{cp.name} - Victoire achetee"
        self.game_over   = True
        self._set_msg(f"{cp.name} a paye pour gagner !", C_ACCENT)

    def _ai_play(self):
        move = self.chess.currentPlayer.get_move()
        if move:
            piece, dest = move
            promo_row = 8 if piece.color == WHITE else 1
            promo = Queen if isinstance(piece, Pawn) and dest.row == promo_row else None
            self.chess.apply_move_pieces(piece, dest, promotion_choice=promo)
            self._post_move()

    def _promotion_dialog(self):
        choices = [('Q', 'Reine', Queen), ('R', 'Tour', Rook),
                   ('B', 'Fou', Bishop), ('N', 'Cavalier', Knight)]
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        bw, bh   = 110, 90
        total_w  = len(choices) * (bw + 10) - 10
        start_x  = WIN_W // 2 - total_w // 2
        y        = WIN_H // 2 - bh // 2
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for i, (letter, name, cls) in enumerate(choices):
                        bx = start_x + i * (bw + 10)
                        if bx < mx < bx + bw and y < my < y + bh: return cls
            self.screen.blit(overlay, (0, 0))
            t = self.fnt_title.render("Promotion - choisissez :", True, C_ACCENT)
            self.screen.blit(t, (WIN_W // 2 - t.get_width() // 2, y - 45))
            mx_c, my_c = pygame.mouse.get_pos()
            for i, (letter, name, cls) in enumerate(choices):
                bx  = start_x + i * (bw + 10)
                hov = bx < mx_c < bx + bw and y < my_c < y + bh
                pygame.draw.rect(self.screen, C_ACCENT if hov else C_BTN,
                                 (bx, y, bw, bh), border_radius=10)
                img = self._piece_imgs.get((letter, self.chess.currentPlayer.color))
                if img:
                    sc = pygame.transform.smoothscale(img, (50, 50))
                    self.screen.blit(sc, (bx + bw // 2 - 25, y + 5))
                lbl = self.fnt_panel.render(name, True, (20, 20, 20) if hov else C_TEXT)
                self.screen.blit(lbl, (bx + bw // 2 - lbl.get_width() // 2, y + bh - 22))
            pygame.display.flip()
            self.clock.tick(60)

    def _save(self):
        self.chess.save(SAVE_FILE)
        self._set_msg(f"Sauvegarde dans {SAVE_FILE}", C_ACCENT)

    def _load(self):
        result = Chess.load_from_file(SAVE_FILE)
        if result:
            self.chess = result
            self.selected = None; self.legal_dests = []; self.game_over = False
            self._set_msg("Partie chargee !", C_ACCENT)
        else:
            self._set_msg(f"Aucun fichier {SAVE_FILE}.", C_CHECK)

    def _draw(self):
        self.screen.fill(C_BG)
        self._draw_board()
        self._draw_panel()
        if self.game_over:
            self._draw_gameover()
        if self.screamer_active and self.screamer_surface:
            self.screen.blit(self.screamer_surface, (0, 0))
        if self.ptw_active:
            self._pay_to_win_draw()

    def _draw_board(self):
        board = self.chess.board
        king_check_pos = None
        if self.chess.mode != MODE_ANTICHESS and board.is_in_check(self.chess.currentPlayer.color):
            k = board.find_king(self.chess.currentPlayer.color)
            if k: king_check_pos = k.position

        for ri in range(8):
            for ci in range(8):
                pos = Position.from_idx(ci, ri)
                x, y = sq_to_px(ci, ri, self.flipped)
                pygame.draw.rect(self.screen,
                                 C_LIGHT if (ci + ri) % 2 == 0 else C_DARK,
                                 (x, y, SQ, SQ))
                if king_check_pos and pos == king_check_pos:
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                    s.fill((*C_CHECK, 140)); self.screen.blit(s, (x, y))
                if self.selected and self.selected.position == pos:
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                    s.fill((*C_SEL, 130)); self.screen.blit(s, (x, y))
                if pos in self.legal_dests:
                    if board.get_piece(pos):
                        pygame.draw.rect(self.screen, C_MOVE, (x, y, SQ, SQ), 4)
                    else:
                        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*C_MOVE, 130), (SQ // 2, SQ // 2), SQ // 5)
                        self.screen.blit(s, (x, y))
                piece = board.get_piece(pos)
                if piece:
                    img = self._piece_imgs.get((str(piece), piece.color))
                    if img:
                        iw, ih = img.get_size()
                        self.screen.blit(img, (x + (SQ - iw) // 2, y + (SQ - ih) // 2))

        for i in range(8):
            lbl = self.fnt_coord.render(
                COLS[i] if not self.flipped else COLS[7 - i], True, (100, 100, 100))
            self.screen.blit(lbl, (i * SQ + SQ - lbl.get_width() - 3, BOARD_PX - lbl.get_height() - 2))
            r = str(8 - i) if not self.flipped else str(i + 1)
            self.screen.blit(self.fnt_coord.render(r, True, (100, 100, 100)), (3, i * SQ + 3))

    def _draw_panel(self):
        px = BOARD_PX
        pygame.draw.rect(self.screen, C_PANEL, (px, 0, PANEL_W, WIN_H))
        pygame.draw.line(self.screen, C_ACCENT, (px, 0), (px, WIN_H), 2)
        y = 10
        t = self.fnt_title.render("Jeu d'Echecs", True, C_ACCENT)
        self.screen.blit(t, (px + PANEL_W // 2 - t.get_width() // 2, y)); y += 24

        mode_col = {MODE_CLASSIC: (100,160,60), MODE_CHESS960: (180,110,40),
                    MODE_CHAOS: (160,60,200), MODE_ANTICHESS: (200,40,40)}
        mode_lbl = {MODE_CLASSIC: "Classique", MODE_CHESS960: "Chess 960",
                    MODE_CHAOS: "Chaos", MODE_ANTICHESS: "Anti-Echecs"}
        mc = mode_col.get(self.chess.mode, C_ACCENT)
        ml = mode_lbl.get(self.chess.mode, self.chess.mode)
        mt = self.fnt_coord.render(f"[ Mode : {ml} ]", True, mc)
        self.screen.blit(mt, (px + PANEL_W // 2 - mt.get_width() // 2, y)); y += 18
        pygame.draw.line(self.screen, (70, 70, 70), (px + 6, y), (px + PANEL_W - 6, y)); y += 6

        for p in self.chess.players:
            arrow = "> " if p == self.chess.currentPlayer else "  "
            col   = C_ACCENT if p == self.chess.currentPlayer else (150, 150, 150)
            sym   = "B" if p.color == WHITE else "N"
            ai    = " [IA]" if p.is_ai() else ""
            count = len(self.chess.board.all_pieces(p.color))
            lbl   = self.fnt_panel.render(f"{arrow}[{sym}] {p.name}{ai}  ({count})", True, col)
            self.screen.blit(lbl, (px + 8, y)); y += 20
        y += 4
        pygame.draw.line(self.screen, (70, 70, 70), (px + 6, y), (px + PANEL_W - 6, y)); y += 6

        max_w = PANEL_W - 16; words = self.message.split(); line = ""
        for word in words:
            test = (line + " " + word).strip()
            if self.fnt_panel.size(test)[0] > max_w:
                s = self.fnt_panel.render(line, True, self.msg_color)
                self.screen.blit(s, (px + 8, y)); y += 17; line = word
            else:
                line = test
        if line:
            s = self.fnt_panel.render(line, True, self.msg_color)
            self.screen.blit(s, (px + 8, y)); y += 17
        y += 4
        pygame.draw.line(self.screen, (70, 70, 70), (px + 6, y), (px + PANEL_W - 6, y)); y += 6

        h_lbl = self.fnt_coord.render("Historique :", True, (110, 110, 110))
        self.screen.blit(h_lbl, (px + 8, y)); y += 15
        for entry in self.chess._history[-8:]:
            s = self.fnt_coord.render(f"  {entry}", True, (160, 160, 160))
            self.screen.blit(s, (px + 8, y)); y += 14

        shortcuts = [("S", "Sauvegarder"), ("L", "Charger"), ("F", "Retourner"),
                     ("R", "Recharger imgs"), ("Esc", "Deselect.")]
        sy = WIN_H - 215
        pygame.draw.line(self.screen, (70, 70, 70), (px + 6, sy - 4), (px + PANEL_W - 6, sy - 4))
        for key, desc in shortcuts:
            k = self.fnt_coord.render(f"[{key}]", True, C_ACCENT)
            d = self.fnt_coord.render(desc, True, (140, 140, 140))
            self.screen.blit(k, (px + 8, sy)); self.screen.blit(d, (px + 34, sy)); sy += 13

        self.btn_save.draw(self.screen, self.fnt_panel)
        self.btn_load.draw(self.screen, self.fnt_panel)
        self.btn_flip.draw(self.screen, self.fnt_panel)
        self.btn_skin.draw(self.screen, self.fnt_panel)
        self.btn_ptw.draw(self.screen,  self.fnt_panel)

    def _draw_gameover(self):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170)); self.screen.blit(ov, (0, 0))
        if self.chess.mode == MODE_ANTICHESS:
            headline = "TOUTES LES PIECES PERDUES !"
        elif "achetee" in self.winner_name:
            headline = "VICTOIRE ACHETEE !"
        elif "Personne" in self.winner_name:
            headline = "PAT !"
        else:
            headline = "ECHEC ET MAT !"
        t1 = self.fnt_big.render(headline, True, C_ACCENT)
        t2 = self.fnt_title.render(f"Vainqueur : {self.winner_name}", True, C_TEXT)
        t3 = self.fnt_lbl.render("Fermez ou lancez une nouvelle partie.", True, (130, 130, 130))
        cx, cy = WIN_W // 2, WIN_H // 2
        self.screen.blit(t1, (cx - t1.get_width() // 2, cy - 55))
        self.screen.blit(t2, (cx - t2.get_width() // 2, cy + 10))
        self.screen.blit(t3, (cx - t3.get_width() // 2, cy + 55))

    def run(self):
        if not os.path.exists(PIECES_DIR):
            os.makedirs(PIECES_DIR, exist_ok=True)
            with open(os.path.join(PIECES_DIR, "README.txt"), "w") as f:
                f.write("Placez ici vos PNG (80x80) — wK.png, bQ.png, etc.\n"
                        "Appuyez sur [R] pour recharger.\n")
        self.run_menu()
        self.run_game()


if __name__ == "__main__":
    app = ChessApp()
    app.run()
