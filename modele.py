from constantes import *
from abc import ABC, abstractmethod

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


