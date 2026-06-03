from piece import Piece
from position import Position


# le roi peut bouger d'une seule case dans toutes les directions
class King(Piece):
    def __init__(self, position, color):
        super().__init__(position, color)
        self.a_bouge = False  # pour le roque

    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()

        # le roi bouge d'une seule case
        if abs(col_new - col_actuel) > 1 or abs(row_new - row_actuel) > 1:
            return False

        # on peut pas manger sa propre piece
        piece_dest = board.getPiece(newPosition)
        if piece_dest != None and piece_dest.get_color() == self.color:
            return False
        return True

    def __str__(self):
        return "K"


# la reine peut bouger en ligne droite ou en diagonale
class Queen(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        diff_col = abs(col_new - col_actuel)
        diff_row = abs(row_new - row_actuel)

        # mouvement invalide si c'est pas une ligne droite ou une diagonale
        if col_actuel != col_new and row_actuel != row_new and diff_col != diff_row:
            return False

        piece_dest = board.getPiece(newPosition)
        if piece_dest != None and piece_dest.get_color() == self.color:
            return False

        # on verifie qu'il y a pas de pieces sur le chemin
        if col_actuel == col_new:
            step = 1 if row_new > row_actuel else -1
            for r in range(row_actuel + step, row_new, step):
                if board.getPiece(Position(self.position.get_column(), r)) != None:
                    return False
        elif row_actuel == row_new:
            step = 1 if col_new > col_actuel else -1
            for c in range(col_actuel + step, col_new, step):
                if board.getPiece(Position(chr(ord('a') + c), row_actuel)) != None:
                    return False
        else:
            step_col = 1 if col_new > col_actuel else -1
            step_row = 1 if row_new > row_actuel else -1
            c = col_actuel + step_col
            r = row_actuel + step_row
            while c != col_new and r != row_new:
                if board.getPiece(Position(chr(ord('a') + c), r)) != None:
                    return False
                c += step_col
                r += step_row
        return True

    def __str__(self):
        return "Q"


# le fou se deplace en diagonale
class Bishop(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()

        # mouvement diagonal obligatoire
        if abs(col_new - col_actuel) != abs(row_new - row_actuel):
            return False

        piece_dest = board.getPiece(newPosition)
        if piece_dest != None and piece_dest.get_color() == self.color:
            return False

        step_col = 1 if col_new > col_actuel else -1
        step_row = 1 if row_new > row_actuel else -1
        c = col_actuel + step_col
        r = row_actuel + step_row
        while c != col_new and r != row_new:
            if board.getPiece(Position(chr(ord('a') + c), r)) != None:
                return False
            c += step_col
            r += step_row
        return True

    def __str__(self):
        return "B"


# le cavalier fait un L
class Knight(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        diff_col = abs(col_new - col_actuel)
        diff_row = abs(row_new - row_actuel)

        # mouvement en L : 2+1 ou 1+2
        if not ((diff_col == 2 and diff_row == 1) or (diff_col == 1 and diff_row == 2)):
            return False

        piece_dest = board.getPiece(newPosition)
        if piece_dest != None and piece_dest.get_color() == self.color:
            return False
        return True

    def __str__(self):
        return "N"


# la tour se deplace en ligne droite
class Rook(Piece):
    def __init__(self, position, color):
        super().__init__(position, color)
        self.a_bouge = False

    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()

        # la tour bouge que en ligne droite
        if col_actuel != col_new and row_actuel != row_new:
            return False

        piece_dest = board.getPiece(newPosition)
        if piece_dest != None and piece_dest.get_color() == self.color:
            return False

        # verification des pieces sur le chemin
        if col_actuel == col_new:
            step = 1 if row_new > row_actuel else -1
            for r in range(row_actuel + step, row_new, step):
                if board.getPiece(Position(self.position.get_column(), r)) != None:
                    return False
        else:
            step = 1 if col_new > col_actuel else -1
            for c in range(col_actuel + step, col_new, step):
                if board.getPiece(Position(chr(ord('a') + c), row_actuel)) != None:
                    return False
        return True

    def __str__(self):
        return "R"


# le pion avance et mange en diagonale
class Pawn(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.position.get_column()) - ord('a')
        row_actuel = self.position.get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()

        # les blancs vont vers le haut et les noirs vers le bas
        direction = 1 if self.color == 0 else -1
        depart = 2 if self.color == 0 else 7

        # avancer tout droit
        if col_actuel == col_new:
            if row_new == row_actuel + direction:
                if board.getPiece(newPosition) is None:
                    return True
            # au depart on peut avancer de 2 cases
            if row_actuel == depart and row_new == row_actuel + 2 * direction:
                case_milieu = Position(self.position.get_column(), row_actuel + direction)
                if board.getPiece(newPosition) is None and board.getPiece(case_milieu) is None:
                    return True

        # manger en diagonale
        if abs(col_new - col_actuel) == 1 and row_new == row_actuel + direction:
            piece_dest = board.getPiece(newPosition)
            if piece_dest != None and piece_dest.get_color() != self.color:
                return True
            # prise en passant
            ep = board.get_en_passant()
            if ep != None and newPosition == ep:
                return True
        return False

    def __str__(self):
        return "P"


# dictionnaire pour creer les pieces depuis leur lettre
CORRESPONDANCE = {'K': King, 'Q': Queen, 'B': Bishop, 'N': Knight, 'R': Rook, 'P': Pawn}

# dictionnaire pour les symboles unicode des pieces
SYMBOLES = {
    ('K', 0): '♔', ('Q', 0): '♕', ('R', 0): '♖',
    ('B', 0): '♗', ('N', 0): '♘', ('P', 0): '♙',
    ('K', 1): '♚', ('Q', 1): '♛', ('R', 1): '♜',
    ('B', 1): '♝', ('N', 1): '♞', ('P', 1): '♟',
}
