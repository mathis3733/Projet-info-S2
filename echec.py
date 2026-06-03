import tkinter as tk
import json
import os
from PIL import Image, ImageTk

TAILLE = 70
CLAIR = "#F0D9B5"
FONCE = "#B58863"
SELECTIONNE = "#7FC97F"
POSSIBLE = "#AAD4AA"
ECHEC_COLOR = "#E05555"

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


class Position:
    def __init__(self, column, row):
        self.__column = column
        self.__row = row

    def get_column(self):
        return self.__column

    def get_row(self):
        return self.__row

    def __str__(self):
        return self.__column + str(self.__row)

    def __eq__(self, other):
        return self.__column == other.get_column() and self.__row == other.get_row()


class Piece:
    def __init__(self, position, color):
        self.__position = position
        self.__color = color

    def get_position(self):
        return self.__position

    def set_position(self, position):
        self.__position = position

    def get_color(self):
        return self.__color

    def isValidMove(self, newPosition, board):
        return True

    def __str__(self):
        return "?"


class King(Piece):
    def __init__(self, position, color):
        super().__init__(position, color)
        self.__a_bouge = False

    def a_bouge(self):
        return self.__a_bouge

    def set_a_bouge(self, val):
        self.__a_bouge = val

    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        if abs(col_new - col_actuel) > 1 or abs(row_new - row_actuel) > 1:
            return False
        piece_dest = board.getPiece(newPosition)
        if piece_dest is not None and piece_dest.get_color() == self.get_color():
            return False
        return True

    def __str__(self):
        return "K"


class Queen(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        diff_col = abs(col_new - col_actuel)
        diff_row = abs(row_new - row_actuel)
        if col_actuel != col_new and row_actuel != row_new and diff_col != diff_row:
            return False
        piece_dest = board.getPiece(newPosition)
        if piece_dest is not None and piece_dest.get_color() == self.get_color():
            return False
        if col_actuel == col_new:
            step = 1 if row_new > row_actuel else -1
            for r in range(row_actuel + step, row_new, step):
                if board.getPiece(Position(self.get_position().get_column(), r)) is not None:
                    return False
        elif row_actuel == row_new:
            step = 1 if col_new > col_actuel else -1
            for c in range(col_actuel + step, col_new, step):
                if board.getPiece(Position(chr(ord('a') + c), row_actuel)) is not None:
                    return False
        else:
            step_col = 1 if col_new > col_actuel else -1
            step_row = 1 if row_new > row_actuel else -1
            c = col_actuel + step_col
            r = row_actuel + step_row
            while c != col_new and r != row_new:
                if board.getPiece(Position(chr(ord('a') + c), r)) is not None:
                    return False
                c += step_col
                r += step_row
        return True

    def __str__(self):
        return "Q"


class Bishop(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        if abs(col_new - col_actuel) != abs(row_new - row_actuel):
            return False
        piece_dest = board.getPiece(newPosition)
        if piece_dest is not None and piece_dest.get_color() == self.get_color():
            return False
        step_col = 1 if col_new > col_actuel else -1
        step_row = 1 if row_new > row_actuel else -1
        c = col_actuel + step_col
        r = row_actuel + step_row
        while c != col_new and r != row_new:
            if board.getPiece(Position(chr(ord('a') + c), r)) is not None:
                return False
            c += step_col
            r += step_row
        return True

    def __str__(self):
        return "B"


class Knight(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        diff_col = abs(col_new - col_actuel)
        diff_row = abs(row_new - row_actuel)
        if not ((diff_col == 2 and diff_row == 1) or (diff_col == 1 and diff_row == 2)):
            return False
        piece_dest = board.getPiece(newPosition)
        if piece_dest is not None and piece_dest.get_color() == self.get_color():
            return False
        return True

    def __str__(self):
        return "N"


class Rook(Piece):
    def __init__(self, position, color):
        super().__init__(position, color)
        self.__a_bouge = False

    def a_bouge(self):
        return self.__a_bouge

    def set_a_bouge(self, val):
        self.__a_bouge = val

    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        if col_actuel != col_new and row_actuel != row_new:
            return False
        piece_dest = board.getPiece(newPosition)
        if piece_dest is not None and piece_dest.get_color() == self.get_color():
            return False
        if col_actuel == col_new:
            step = 1 if row_new > row_actuel else -1
            for r in range(row_actuel + step, row_new, step):
                if board.getPiece(Position(self.get_position().get_column(), r)) is not None:
                    return False
        else:
            step = 1 if col_new > col_actuel else -1
            for c in range(col_actuel + step, col_new, step):
                if board.getPiece(Position(chr(ord('a') + c), row_actuel)) is not None:
                    return False
        return True

    def __str__(self):
        return "R"


class Pawn(Piece):
    def isValidMove(self, newPosition, board):
        col_actuel = ord(self.get_position().get_column()) - ord('a')
        row_actuel = self.get_position().get_row()
        col_new = ord(newPosition.get_column()) - ord('a')
        row_new = newPosition.get_row()
        direction = 1 if self.get_color() == 0 else -1
        depart = 2 if self.get_color() == 0 else 7
        if col_actuel == col_new:
            if row_new == row_actuel + direction:
                if board.getPiece(newPosition) is None:
                    return True
            if row_actuel == depart and row_new == row_actuel + 2 * direction:
                case_milieu = Position(self.get_position().get_column(), row_actuel + direction)
                if board.getPiece(newPosition) is None and board.getPiece(case_milieu) is None:
                    return True
        if abs(col_new - col_actuel) == 1 and row_new == row_actuel + direction:
            piece_dest = board.getPiece(newPosition)
            if piece_dest is not None and piece_dest.get_color() != self.get_color():
                return True
            ep = board.get_en_passant()
            if ep is not None and newPosition == ep:
                return True
        return False

    def __str__(self):
        return "P"


CORRESPONDANCE = {'K': King, 'Q': Queen, 'B': Bishop, 'N': Knight, 'R': Rook, 'P': Pawn}
SYMBOLES = {
    ('K', 0): '♔', ('Q', 0): '♕', ('R', 0): '♖',
    ('B', 0): '♗', ('N', 0): '♘', ('P', 0): '♙',
    ('K', 1): '♚', ('Q', 1): '♛', ('R', 1): '♜',
    ('B', 1): '♝', ('N', 1): '♞', ('P', 1): '♟',
}


class Board:
    def __init__(self):
        self.__pieces = []
        self.__en_passant = None
        self.__init_plateau()

    def __init_plateau(self):
        ordre = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        colonnes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i, classe in enumerate(ordre):
            self.__pieces.append(classe(Position(colonnes[i], 1), 0))
            self.__pieces.append(classe(Position(colonnes[i], 8), 1))
        for col in colonnes:
            self.__pieces.append(Pawn(Position(col, 2), 0))
            self.__pieces.append(Pawn(Position(col, 7), 1))

    def getPosition(self, piece):
        for p in self.__pieces:
            if p is piece:
                return p.get_position()
        return None

    def getPiece(self, position):
        for p in self.__pieces:
            if p.get_position() == position:
                return p
        return None

    def get_pieces(self):
        return self.__pieces

    def supprimer_piece(self, position):
        for i, p in enumerate(self.__pieces):
            if p.get_position() == position:
                self.__pieces.pop(i)
                return

    def get_en_passant(self):
        return self.__en_passant

    def set_en_passant(self, pos):
        self.__en_passant = pos

    def get_roi(self, color):
        for p in self.__pieces:
            if isinstance(p, King) and p.get_color() == color:
                return p
        return None

    def est_en_echec(self, color):
        roi = self.get_roi(color)
        if roi is None:
            return False
        for p in self.__pieces:
            if p.get_color() != color:
                if p.isValidMove(roi.get_position(), self):
                    return True
        return False

    def simuler_move(self, pos_orig, pos_dest):
        nouvelle_board = Board.__new__(Board)
        nouvelle_board._Board__pieces = []
        nouvelle_board._Board__en_passant = None
        ep = self.__en_passant
        for p in self.__pieces:
            if p.get_position() == pos_dest:
                continue
            if ep is not None and isinstance(p, Pawn) and p.get_position() == Position(pos_dest.get_column(), pos_orig.get_row()) and pos_dest == ep:
                continue
            nouvelle_piece = p.__class__.__new__(p.__class__)
            nouvelle_piece._Piece__position = Position(p.get_position().get_column(), p.get_position().get_row())
            nouvelle_piece._Piece__color = p.get_color()
            if isinstance(p, King):
                nouvelle_piece._King__a_bouge = p.a_bouge()
            if isinstance(p, Rook):
                nouvelle_piece._Rook__a_bouge = p.a_bouge()
            if p.get_position() == pos_orig:
                nouvelle_piece._Piece__position = Position(pos_dest.get_column(), pos_dest.get_row())
            nouvelle_board._Board__pieces.append(nouvelle_piece)
        return nouvelle_board

    def peut_roquer_petit(self, color):
        row = 1 if color == 0 else 8
        roi = self.getPiece(Position('e', row))
        tour = self.getPiece(Position('h', row))
        if not isinstance(roi, King) or roi.a_bouge():
            return False
        if not isinstance(tour, Rook) or tour.a_bouge():
            return False
        for col in ['f', 'g']:
            if self.getPiece(Position(col, row)) is not None:
                return False
        if self.est_en_echec(color):
            return False
        for col in ['f', 'g']:
            b = self.simuler_move(Position('e', row), Position(col, row))
            if b.est_en_echec(color):
                return False
        return True

    def peut_roquer_grand(self, color):
        row = 1 if color == 0 else 8
        roi = self.getPiece(Position('e', row))
        tour = self.getPiece(Position('a', row))
        if not isinstance(roi, King) or roi.a_bouge():
            return False
        if not isinstance(tour, Rook) or tour.a_bouge():
            return False
        for col in ['b', 'c', 'd']:
            if self.getPiece(Position(col, row)) is not None:
                return False
        if self.est_en_echec(color):
            return False
        for col in ['c', 'd']:
            b = self.simuler_move(Position('e', row), Position(col, row))
            if b.est_en_echec(color):
                return False
        return True


class Player:
    def __init__(self, name, color):
        self.__name = name
        self.__color = color

    def get_name(self):
        return self.__name

    def get_color(self):
        return self.__color


class Chess:
    def __init__(self):
        self.__board = Board()
        self.__players = [Player("Blancs", 0), Player("Noirs", 1)]
        self.__currentPlayer = self.__players[0]
        self.__selected = None
        self.__partie_terminee = False

    def get_board(self):
        return self.__board

    def get_current_player(self):
        return self.__currentPlayer

    def get_selected(self):
        return self.__selected

    def set_selected(self, pos):
        self.__selected = pos

    def partie_terminee(self):
        return self.__partie_terminee

    def isValidMove(self, pos_orig, pos_dest):
        piece = self.__board.getPiece(pos_orig)
        if piece is None:
            return False
        if piece.get_color() != self.__currentPlayer.get_color():
            return False
        if pos_orig == pos_dest:
            return False
        if not piece.isValidMove(pos_dest, self.__board):
            return False
        board_apres = self.__board.simuler_move(pos_orig, pos_dest)
        if board_apres.est_en_echec(self.__currentPlayer.get_color()):
            return False
        return True

    def isValidRoque(self, pos_dest):
        color = self.__currentPlayer.get_color()
        row = 1 if color == 0 else 8
        if pos_dest == Position('g', row) and self.__board.peut_roquer_petit(color):
            return "petit"
        if pos_dest == Position('c', row) and self.__board.peut_roquer_grand(color):
            return "grand"
        return None

    def updateBoard(self, pos_orig, pos_dest):
        piece = self.__board.getPiece(pos_orig)
        roque = None
        if isinstance(piece, King):
            roque = self.isValidRoque(pos_dest)

        ep = self.__board.get_en_passant()
        self.__board.set_en_passant(None)

        if isinstance(piece, Pawn):
            row_orig = pos_orig.get_row()
            row_dest = pos_dest.get_row()
            if abs(row_dest - row_orig) == 2:
                direction = 1 if piece.get_color() == 0 else -1
                self.__board.set_en_passant(Position(pos_orig.get_column(), row_orig + direction))
            if ep is not None and pos_dest == ep:
                self.__board.supprimer_piece(Position(pos_dest.get_column(), pos_orig.get_row()))

        self.__board.supprimer_piece(pos_dest)
        piece.set_position(pos_dest)

        if isinstance(piece, King):
            piece.set_a_bouge(True)
            if roque == "petit":
                row = pos_dest.get_row()
                tour = self.__board.getPiece(Position('h', row))
                if tour:
                    tour.set_position(Position('f', row))
                    tour.set_a_bouge(True)
            elif roque == "grand":
                row = pos_dest.get_row()
                tour = self.__board.getPiece(Position('a', row))
                if tour:
                    tour.set_position(Position('d', row))
                    tour.set_a_bouge(True)

        if isinstance(piece, Rook):
            piece.set_a_bouge(True)

        if isinstance(piece, Pawn):
            row_fin = 8 if piece.get_color() == 0 else 1
            if pos_dest.get_row() == row_fin:
                return "promotion"
        return None

    def promouvoir(self, pos, classe):
        for i, p in enumerate(self.__board.get_pieces()):
            if p.get_position() == pos:
                nouvelle = classe(pos, p.get_color())
                self.__board.get_pieces()[i] = nouvelle
                return

    def switchPlayer(self):
        if self.__currentPlayer == self.__players[0]:
            self.__currentPlayer = self.__players[1]
        else:
            self.__currentPlayer = self.__players[0]

    def verifier_fin(self):
        color = self.__currentPlayer.get_color()
        colonnes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for p in self.__board.get_pieces():
            if p.get_color() == color:
                for col in colonnes:
                    for row in range(1, 9):
                        pos_dest = Position(col, row)
                        if p.get_position() == pos_dest:
                            continue
                        if not p.isValidMove(pos_dest, self.__board):
                            continue
                        board_apres = self.__board.simuler_move(p.get_position(), pos_dest)
                        if not board_apres.est_en_echec(color):
                            return None
        if self.__board.est_en_echec(color):
            self.__partie_terminee = True
            return "Echec et mat ! Les " + ("Noirs" if color == 0 else "Blancs") + " gagnent !"
        else:
            self.__partie_terminee = True
            return "Pat ! Match nul."

    def est_en_echec(self):
        return self.__board.est_en_echec(self.__currentPlayer.get_color())

    def sauvegarder(self, fichier="sauvegarde.json"):
        data = {"pieces": [], "currentPlayer": self.__players.index(self.__currentPlayer)}
        for p in self.__board.get_pieces():
            d = {
                "type": str(p),
                "col": p.get_position().get_column(),
                "row": p.get_position().get_row(),
                "color": p.get_color()
            }
            if isinstance(p, King):
                d["a_bouge"] = p.a_bouge()
            if isinstance(p, Rook):
                d["a_bouge"] = p.a_bouge()
            data["pieces"].append(d)
        with open(fichier, "w") as f:
            json.dump(data, f)

    def charger(self, fichier="sauvegarde.json"):
        with open(fichier, "r") as f:
            data = json.load(f)
        self.__board = Board.__new__(Board)
        self.__board._Board__pieces = []
        for d in data["pieces"]:
            classe = CORRESPONDANCE[d["type"]]
            pos = Position(d["col"], d["row"])
            p = classe(pos, d["color"])
            if isinstance(p, King) and "a_bouge" in d:
                p.set_a_bouge(d["a_bouge"])
            if isinstance(p, Rook) and "a_bouge" in d:
                p.set_a_bouge(d["a_bouge"])
            self.__board._Board__pieces.append(p)
        self.__currentPlayer = self.__players[data["currentPlayer"]]
        self.__partie_terminee = False


def charger_images():
    images = {}
    suffixe = {0: 'w', 1: 'b'}
    for type_piece in ['K', 'Q', 'R', 'B', 'N', 'P']:
        for color in [0, 1]:
            nom = type_piece + suffixe[color] + ".png"
            chemin = os.path.join(IMAGES_DIR, nom)
            if os.path.exists(chemin):
                img = Image.open(chemin).convert("RGBA")
                img = img.resize((TAILLE - 8, TAILLE - 8), Image.LANCZOS)
                images[(type_piece, color)] = ImageTk.PhotoImage(img)
    return images


class App:
    def __init__(self, root):
        self.__root = root
        self.__root.title("Echecs")
        self.__root.resizable(False, False)
        self.__chess = Chess()
        self.__mouvements_valides = []
        self.__images = charger_images()

        self.__label = tk.Label(root, text="Tour des Blancs", font=("Arial", 14))
        self.__label.pack(pady=5)

        self.__canvas = tk.Canvas(root, width=TAILLE * 8, height=TAILLE * 8)
        self.__canvas.pack()
        self.__canvas.bind("<Button-1>", self.__clic)

        frame = tk.Frame(root)
        frame.pack(pady=5)
        tk.Button(frame, text="Sauvegarder", command=self.__sauvegarder).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Charger", command=self.__charger).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Nouvelle partie", command=self.__nouvelle_partie).pack(side=tk.LEFT, padx=5)

        self.__dessiner()

    def __dessiner(self):
        self.__canvas.delete("all")
        colonnes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        selected = self.__chess.get_selected()
        en_echec = self.__chess.est_en_echec()
        roi = self.__chess.get_board().get_roi(self.__chess.get_current_player().get_color())
        pos_roi = roi.get_position() if roi else None

        for row in range(8):
            for col in range(8):
                x1 = col * TAILLE
                y1 = row * TAILLE
                x2 = x1 + TAILLE
                y2 = y1 + TAILLE
                pos = Position(colonnes[col], 8 - row)

                if en_echec and pos_roi and pos == pos_roi:
                    couleur = ECHEC_COLOR
                elif selected and pos == selected:
                    couleur = SELECTIONNE
                elif pos in self.__mouvements_valides:
                    couleur = POSSIBLE
                elif (row + col) % 2 == 0:
                    couleur = CLAIR
                else:
                    couleur = FONCE

                self.__canvas.create_rectangle(x1, y1, x2, y2, fill=couleur, outline="")

                piece = self.__chess.get_board().getPiece(pos)
                if piece is not None:
                    cle = (str(piece), piece.get_color())
                    if cle in self.__images:
                        self.__canvas.create_image(
                            x1 + TAILLE // 2, y1 + TAILLE // 2,
                            image=self.__images[cle]
                        )
                    else:
                        self.__canvas.create_text(
                            x1 + TAILLE // 2, y1 + TAILLE // 2,
                            text=SYMBOLES[cle], font=("Arial", int(TAILLE * 0.6))
                        )

        couleur_nom = "Blancs" if self.__chess.get_current_player().get_color() == 0 else "Noirs"
        if en_echec and not self.__chess.partie_terminee():
            self.__label.config(text="⚠ Echec ! Tour des " + couleur_nom, fg="red")
        else:
            self.__label.config(text="Tour des " + couleur_nom, fg="black")

    def __clic(self, event):
        if self.__chess.partie_terminee():
            return
        colonnes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        col = event.x // TAILLE
        row = event.y // TAILLE
        if col < 0 or col > 7 or row < 0 or row > 7:
            return
        pos_clique = Position(colonnes[col], 8 - row)
        selected = self.__chess.get_selected()

        if selected is None:
            piece = self.__chess.get_board().getPiece(pos_clique)
            if piece is not None and piece.get_color() == self.__chess.get_current_player().get_color():
                self.__chess.set_selected(pos_clique)
                self.__mouvements_valides = self.__calculer_mouvements(pos_clique)
        else:
            if self.__chess.isValidMove(selected, pos_clique):
                resultat = self.__chess.updateBoard(selected, pos_clique)
                if resultat == "promotion":
                    self.__dessiner()
                    self.__demander_promotion(pos_clique)
                    return
                self.__chess.switchPlayer()
                self.__chess.set_selected(None)
                self.__mouvements_valides = []
                self.__dessiner()
                self.__verifier_fin()
                return
            else:
                piece = self.__chess.get_board().getPiece(pos_clique)
                if piece is not None and piece.get_color() == self.__chess.get_current_player().get_color():
                    self.__chess.set_selected(pos_clique)
                    self.__mouvements_valides = self.__calculer_mouvements(pos_clique)
                else:
                    self.__chess.set_selected(None)
                    self.__mouvements_valides = []

        self.__dessiner()

    def __demander_promotion(self, pos):
        couleur = self.__chess.get_current_player().get_color()
        popup = tk.Toplevel(self.__root)
        popup.title("Promotion !")
        popup.resizable(False, False)
        popup.grab_set()
        tk.Label(popup, text="Choisissez la pièce :", font=("Arial", 12)).pack(pady=8)
        frame = tk.Frame(popup)
        frame.pack(pady=5)
        choix = [("Reine", Queen), ("Tour", Rook), ("Fou", Bishop), ("Cavalier", Knight)]
        for nom, classe in choix:
            cle = (str(classe(Position('a', 1), couleur)), couleur)
            def choisir(c=classe):
                self.__chess.promouvoir(pos, c)
                popup.destroy()
                self.__chess.switchPlayer()
                self.__chess.set_selected(None)
                self.__mouvements_valides = []
                self.__dessiner()
                self.__verifier_fin()
            btn = tk.Button(frame, text=nom, width=8, font=("Arial", 11), command=choisir)
            if cle in self.__images:
                btn.config(image=self.__images[cle], compound=tk.TOP)
            btn.pack(side=tk.LEFT, padx=4)

    def __verifier_fin(self):
        resultat = self.__chess.verifier_fin()
        if resultat is not None:
            self.__label.config(text=resultat, fg="blue")
            self.__canvas.unbind("<Button-1>")

    def __calculer_mouvements(self, pos_orig):
        colonnes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        valides = []
        color = self.__chess.get_current_player().get_color()
        for col in colonnes:
            for row in range(1, 9):
                pos = Position(col, row)
                if self.__chess.isValidMove(pos_orig, pos):
                    valides.append(pos)
        piece = self.__chess.get_board().getPiece(pos_orig)
        if isinstance(piece, King):
            row = 1 if color == 0 else 8
            if self.__chess.get_board().peut_roquer_petit(color):
                valides.append(Position('g', row))
            if self.__chess.get_board().peut_roquer_grand(color):
                valides.append(Position('c', row))
        return valides

    def __sauvegarder(self):
        self.__chess.sauvegarder()

    def __charger(self):
        self.__chess.charger()
        self.__chess.set_selected(None)
        self.__mouvements_valides = []
        self.__canvas.bind("<Button-1>", self.__clic)
        self.__dessiner()

    def __nouvelle_partie(self):
        self.__chess = Chess()
        self.__mouvements_valides = []
        self.__canvas.bind("<Button-1>", self.__clic)
        self.__dessiner()


class PayToWin:
    def __init__(self, chess, app):
        self.chess = chess
        self.app = app
        self.prix = 100

    def acheter_victoire(self):
        popup = tk.Toplevel()
        popup.title("💰 PAY TO WIN 💰")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="💰 PAY TO WIN 💰", font=("Arial", 16, "bold"), fg="gold").pack(pady=10)
        tk.Label(popup, text=f"Gagnez instantanément pour seulement {self.prix}€ !", font=("Arial", 11)).pack()
        tk.Label(popup, text="(offre limitée)", font=("Arial", 9), fg="gray").pack()

        self.entry = tk.Entry(popup, font=("Arial", 13), justify="center")
        self.entry.pack(pady=10)
        self.entry.insert(0, f"Entrez {self.prix}")

        tk.Button(popup, text="💳 PAYER ET GAGNER", font=("Arial", 12, "bold"), bg="green", fg="white",
                  command=lambda: self.valider(popup)).pack(pady=5)
        tk.Button(popup, text="Non merci je préfère perdre", font=("Arial", 8), fg="gray",
                  command=popup.destroy).pack(pady=2)

    def valider(self, popup):
        try:
            montant = float(self.entry.get())
            if montant >= self.prix:
                popup.destroy()
                self.chess._Chess__partie_terminee = True
                nom = self.chess.get_current_player().get_name()
                self.app._App__label.config(
                    text=f"💰 {nom} a payé {montant}€ et a gagné !! 💰", fg="green"
                )
                self.app._App__canvas.unbind("<Button-1>")
                self.app._App__dessiner()
            else:
                tk.Label(popup, text=f"❌ Pas assez... il faut {self.prix}€ minimum !", fg="red").pack()
        except ValueError:
            tk.Label(popup, text="❌ Mettez un vrai montant !", fg="red").pack()


root = tk.Tk()
app = App(root)
ptw = PayToWin(app._App__chess, app)
tk.Button(root, text="💰 Pay to Win", font=("Arial", 10, "bold"), bg="gold",
          command=ptw.acheter_victoire).pack(pady=3)
root.mainloop()
