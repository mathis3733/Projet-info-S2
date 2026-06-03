import json
import sqlite3
from board import Board
from position import Position
from pieces import King, Rook, Pawn, Queen, Bishop, Knight, CORRESPONDANCE
from player import Player


# classe principale qui gere la partie
class Chess:
    def __init__(self):
        self.board = Board()
        self.players = [Player("Blancs", 0), Player("Noirs", 1)]
        self.currentPlayer = self.players[0]
        self.selected = None
        self.partie_finie = False

    def get_board(self):
        return self.board

    def get_current_player(self):
        return self.currentPlayer

    def get_selected(self):
        return self.selected

    def set_selected(self, pos):
        self.selected = pos

    def partie_terminee(self):
        return self.partie_finie

    # verifie si un mouvement est valide
    def isValidMove(self, pos_orig, pos_dest):
        piece = self.board.getPiece(pos_orig)
        if piece is None or piece.get_color() != self.currentPlayer.get_color():
            return False
        if pos_orig == pos_dest:
            return False
        if not piece.isValidMove(pos_dest, self.board):
            return False
        # on verifie que le mouvement ne met pas notre roi en echec
        board_apres = self.board.simuler_move(pos_orig, pos_dest)
        if board_apres.est_en_echec(self.currentPlayer.get_color()):
            return False
        return True

    def isValidRoque(self, pos_dest):
        color = self.currentPlayer.get_color()
        row = 1 if color == 0 else 8
        if pos_dest == Position('g', row) and self.board.peut_roquer_petit(color):
            return "petit"
        if pos_dest == Position('c', row) and self.board.peut_roquer_grand(color):
            return "grand"
        return None

    # met a jour le plateau apres un mouvement
    def updateBoard(self, pos_orig, pos_dest):
        piece = self.board.getPiece(pos_orig)
        roque = None
        if isinstance(piece, King):
            roque = self.isValidRoque(pos_dest)

        ep = self.board.get_en_passant()
        self.board.set_en_passant(None)

        # gestion de la prise en passant et du double pas du pion
        if isinstance(piece, Pawn):
            row_orig = pos_orig.get_row()
            row_dest = pos_dest.get_row()
            if abs(row_dest - row_orig) == 2:
                direction = 1 if piece.get_color() == 0 else -1
                self.board.set_en_passant(Position(pos_orig.get_column(), row_orig + direction))
            if ep != None and pos_dest == ep:
                self.board.supprimer_piece(Position(pos_dest.get_column(), pos_orig.get_row()))

        self.board.supprimer_piece(pos_dest)
        piece.set_position(pos_dest)

        # gestion du roque
        if isinstance(piece, King):
            piece.a_bouge = True
            row = pos_dest.get_row()
            if roque == "petit":
                tour = self.board.getPiece(Position('h', row))
                if tour:
                    tour.set_position(Position('f', row))
                    tour.a_bouge = True
            elif roque == "grand":
                tour = self.board.getPiece(Position('a', row))
                if tour:
                    tour.set_position(Position('d', row))
                    tour.a_bouge = True

        if isinstance(piece, Rook):
            piece.a_bouge = True

        # promotion du pion
        if isinstance(piece, Pawn):
            row_fin = 8 if piece.get_color() == 0 else 1
            if pos_dest.get_row() == row_fin:
                return "promotion"
        return None

    def promouvoir(self, pos, classe):
        for i in range(len(self.board.get_pieces())):
            if self.board.get_pieces()[i].get_position() == pos:
                nouvelle = classe(pos, self.board.get_pieces()[i].get_color())
                self.board.get_pieces()[i] = nouvelle
                return

    def switchPlayer(self):
        if self.currentPlayer == self.players[0]:
            self.currentPlayer = self.players[1]
        else:
            self.currentPlayer = self.players[0]

    # verifie si la partie est terminee (echec et mat ou pat)
    def verifier_fin(self):
        color = self.currentPlayer.get_color()
        colonnes = Position.get_colonnes()
        for p in self.board.get_pieces():
            if p.get_color() == color:
                for col in colonnes:
                    for row in range(1, 9):
                        pos_dest = Position(col, row)
                        if p.get_position() == pos_dest:
                            continue
                        if not p.isValidMove(pos_dest, self.board):
                            continue
                        board_apres = self.board.simuler_move(p.get_position(), pos_dest)
                        if not board_apres.est_en_echec(color):
                            return None

        if self.board.est_en_echec(color):
            self.partie_finie = True
            return "Echec et mat ! Les " + ("Noirs" if color == 0 else "Blancs") + " gagnent !"
        else:
            self.partie_finie = True
            return "Pat ! Match nul."

    def est_en_echec(self):
        return self.board.est_en_echec(self.currentPlayer.get_color())

    # sauvegarde la partie dans une base de donnees sqlite
    def sauvegarder(self):
        conn = sqlite3.connect("sauvegarde.db")
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY,
            current_player INTEGER,
            pieces TEXT
        )""")

        pieces_data = []
        for p in self.board.get_pieces():
            d = {
                "type": str(p),
                "col": p.get_position().get_column(),
                "row": p.get_position().get_row(),
                "color": p.get_color()
            }
            if isinstance(p, (King, Rook)):
                d["a_bouge"] = p.a_bouge
            pieces_data.append(d)

        c.execute("DELETE FROM parties")
        c.execute("INSERT INTO parties (current_player, pieces) VALUES (?, ?)",
                  (self.players.index(self.currentPlayer), json.dumps(pieces_data)))
        conn.commit()
        conn.close()

    # charge la partie depuis la base de donnees
    def charger(self):
        conn = sqlite3.connect("sauvegarde.db")
        c = conn.cursor()
        c.execute("SELECT current_player, pieces FROM parties ORDER BY id DESC LIMIT 1")
        ligne = c.fetchone()
        conn.close()

        if ligne is None:
            return

        current_player_index = ligne[0]
        pieces_data = json.loads(ligne[1])

        self.board = Board.__new__(Board)
        self.board.pieces = []
        self.board.en_passant = None
        for d in pieces_data:
            classe = CORRESPONDANCE[d["type"]]
            pos = Position(d["col"], d["row"])
            p = classe(pos, d["color"])
            if isinstance(p, (King, Rook)) and "a_bouge" in d:
                p.a_bouge = d["a_bouge"]
            self.board.pieces.append(p)
        self.currentPlayer = self.players[current_player_index]
        self.partie_finie = False
