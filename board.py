from position import Position
from pieces import King, Queen, Bishop, Knight, Rook, Pawn


# la classe Board represente le plateau avec toutes les pieces
class Board:
    def __init__(self):
        self.pieces = []         # liste de toutes les pieces
        self.en_passant = None   # pour la prise en passant
        self.init_plateau()

    def init_plateau(self):
        # on met les pieces dans l'ordre sur la premiere et derniere ligne
        ordre = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        colonnes = Position.get_colonnes()
        for i in range(len(ordre)):
            self.pieces.append(ordre[i](Position(colonnes[i], 1), 0))
            self.pieces.append(ordre[i](Position(colonnes[i], 8), 1))
        # les pions
        for col in colonnes:
            self.pieces.append(Pawn(Position(col, 2), 0))
            self.pieces.append(Pawn(Position(col, 7), 1))

    def getPiece(self, position):
        for p in self.pieces:
            if p.get_position() == position:
                return p
        return None

    def get_pieces(self):
        return self.pieces

    def supprimer_piece(self, position):
        for i in range(len(self.pieces)):
            if self.pieces[i].get_position() == position:
                self.pieces.pop(i)
                return

    def get_en_passant(self):
        return self.en_passant

    def set_en_passant(self, pos):
        self.en_passant = pos

    # retourne le roi d'une couleur donnee
    def get_roi(self, color):
        for p in self.pieces:
            if isinstance(p, King) and p.get_color() == color:
                return p
        return None

    # verifie si le roi est en echec
    def est_en_echec(self, color):
        roi = self.get_roi(color)
        if roi is None:
            return False
        for p in self.pieces:
            if p.get_color() != color:
                if p.isValidMove(roi.get_position(), self):
                    return True
        return False

    # simule un mouvement pour voir si ca met le roi en echec
    def simuler_move(self, pos_orig, pos_dest):
        nouvelle_board = Board.__new__(Board)
        nouvelle_board.pieces = []
        nouvelle_board.en_passant = None
        ep = self.en_passant

        for p in self.pieces:
            if p.get_position() == pos_dest:
                continue
            # prise en passant: on enleve le pion capture
            if ep != None and isinstance(p, Pawn) and p.get_position() == Position(pos_dest.get_column(), pos_orig.get_row()) and pos_dest == ep:
                continue

            nouvelle_piece = p.__class__.__new__(p.__class__)
            nouvelle_piece.position = Position(p.get_position().get_column(), p.get_position().get_row())
            nouvelle_piece.color = p.get_color()

            if isinstance(p, King):
                nouvelle_piece.a_bouge = p.a_bouge
            if isinstance(p, Rook):
                nouvelle_piece.a_bouge = p.a_bouge
            if p.get_position() == pos_orig:
                nouvelle_piece.position = Position(pos_dest.get_column(), pos_dest.get_row())
            nouvelle_board.pieces.append(nouvelle_piece)
        return nouvelle_board

    # verifie si le petit roque est possible
    def peut_roquer_petit(self, color):
        row = 1 if color == 0 else 8
        roi = self.getPiece(Position('e', row))
        tour = self.getPiece(Position('h', row))

        if not isinstance(roi, King) or roi.a_bouge:
            return False
        if not isinstance(tour, Rook) or tour.a_bouge:
            return False
        for col in ['f', 'g']:
            if self.getPiece(Position(col, row)) != None:
                return False
        if self.est_en_echec(color):
            return False
        for col in ['f', 'g']:
            b = self.simuler_move(Position('e', row), Position(col, row))
            if b.est_en_echec(color):
                return False
        return True

    # verifie si le grand roque est possible
    def peut_roquer_grand(self, color):
        row = 1 if color == 0 else 8
        roi = self.getPiece(Position('e', row))
        tour = self.getPiece(Position('a', row))

        if not isinstance(roi, King) or roi.a_bouge:
            return False
        if not isinstance(tour, Rook) or tour.a_bouge:
            return False
        for col in ['b', 'c', 'd']:
            if self.getPiece(Position(col, row)) != None:
                return False
        if self.est_en_echec(color):
            return False
        for col in ['c', 'd']:
            b = self.simuler_move(Position('e', row), Position(col, row))
            if b.est_en_echec(color):
                return False
        return True
