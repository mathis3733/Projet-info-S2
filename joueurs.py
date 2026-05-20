from constantes import *
from modele import Board, Piece, Queen, Pawn

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


