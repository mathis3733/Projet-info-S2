import tkinter as tk
import os
from PIL import Image, ImageTk
from position import Position
from pieces import King, Queen, Rook, Bishop, Knight, SYMBOLES
from chess import Chess
from player import AIPlayer

# les couleurs du plateau
TAILLE = 70
CLAIR = "#F0D9B5"
FONCE = "#B58863"
SELECTIONNE = "#7FC97F"
POSSIBLE = "#AAD4AA"
ECHEC_COLOR = "#E05555"

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


# interface graphique avec tkinter
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Echecs")
        self.root.resizable(False, False)
        self.chess = Chess()
        self.mouvements_valides = []
        self.images = self.charger_images()
        self.ai_active = False  # est ce que l'IA joue les noirs ?
        self.ai = AIPlayer(1)   # l'IA joue toujours les noirs

        self.label = tk.Label(root, text="Tour des Blancs", font=("Arial", 14))
        self.label.pack(pady=5)

        self.canvas = tk.Canvas(root, width=TAILLE * 8, height=TAILLE * 8)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.clic)

        frame = tk.Frame(root)
        frame.pack(pady=5)
        tk.Button(frame, text="Sauvegarder", command=self.sauvegarder).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Charger", command=self.charger).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Nouvelle partie", command=self.nouvelle_partie).pack(side=tk.LEFT, padx=5)
        self.btn_ai = tk.Button(frame, text="Activer IA", command=self.toggle_ai)
        self.btn_ai.pack(side=tk.LEFT, padx=5)

        self.dessiner()

    # charge les images des pieces depuis le dossier images
    def charger_images(self):
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

    def dessiner(self):
        self.canvas.delete("all")
        colonnes = Position.get_colonnes()
        selected = self.chess.get_selected()
        en_echec = self.chess.est_en_echec()
        roi = self.chess.get_board().get_roi(self.chess.get_current_player().get_color())
        pos_roi = roi.get_position() if roi else None

        for row in range(8):
            for col in range(8):
                x1 = col * TAILLE
                y1 = row * TAILLE
                x2 = x1 + TAILLE
                y2 = y1 + TAILLE
                pos = Position(colonnes[col], 8 - row)

                # choix de la couleur de la case
                if en_echec and pos_roi and pos == pos_roi:
                    couleur = ECHEC_COLOR
                elif selected and pos == selected:
                    couleur = SELECTIONNE
                elif pos in self.mouvements_valides:
                    couleur = POSSIBLE
                elif (row + col) % 2 == 0:
                    couleur = CLAIR
                else:
                    couleur = FONCE

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=couleur, outline="")

                piece = self.chess.get_board().getPiece(pos)
                if piece != None:
                    cle = (str(piece), piece.get_color())
                    if cle in self.images:
                        self.canvas.create_image(x1 + TAILLE // 2, y1 + TAILLE // 2, image=self.images[cle])
                    else:
                        self.canvas.create_text(x1 + TAILLE // 2, y1 + TAILLE // 2, text=SYMBOLES[cle], font=("Arial", int(TAILLE * 0.6)))

        couleur_nom = "Blancs" if self.chess.get_current_player().get_color() == 0 else "Noirs"
        if en_echec and not self.chess.partie_terminee():
            self.label.config(text="Echec ! Tour des " + couleur_nom, fg="red")
        else:
            self.label.config(text="Tour des " + couleur_nom, fg="black")

    def clic(self, event):
        if self.chess.partie_terminee():
            return
        colonnes = Position.get_colonnes()
        col = event.x // TAILLE
        row = event.y // TAILLE
        if not (0 <= col <= 7 and 0 <= row <= 7):
            return

        pos_clique = Position(colonnes[col], 8 - row)
        selected = self.chess.get_selected()

        if selected is None:
            piece = self.chess.get_board().getPiece(pos_clique)
            if piece != None and piece.get_color() == self.chess.get_current_player().get_color():
                self.chess.set_selected(pos_clique)
                self.mouvements_valides = self.calculer_mouvements(pos_clique)
        else:
            if self.chess.isValidMove(selected, pos_clique):
                resultat = self.chess.updateBoard(selected, pos_clique)
                if resultat == "promotion":
                    self.dessiner()
                    self.demander_promotion(pos_clique)
                    return
                self.chess.switchPlayer()
                self.chess.set_selected(None)
                self.mouvements_valides = []
                self.dessiner()
                self.verifier_fin()
                # si l'IA est active et que c'est son tour
                if self.ai_active and self.chess.get_current_player().get_color() == 1 and not self.chess.partie_terminee():
                    self.root.after(400, self.jouer_ia)
                return
            else:
                piece = self.chess.get_board().getPiece(pos_clique)
                if piece != None and piece.get_color() == self.chess.get_current_player().get_color():
                    self.chess.set_selected(pos_clique)
                    self.mouvements_valides = self.calculer_mouvements(pos_clique)
                else:
                    self.chess.set_selected(None)
                    self.mouvements_valides = []
        self.dessiner()

    # fenetre pour choisir la piece lors d'une promotion
    def demander_promotion(self, pos):
        couleur = self.chess.get_current_player().get_color()
        popup = tk.Toplevel(self.root)
        popup.title("Promotion !")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Choisissez la piece :", font=("Arial", 12)).pack(pady=8)
        frame = tk.Frame(popup)
        frame.pack(pady=5)

        choix = [("Reine", Queen), ("Tour", Rook), ("Fou", Bishop), ("Cavalier", Knight)]
        for nom, classe in choix:
            cle = (str(classe(Position('a', 1), couleur)), couleur)
            def choisir(c=classe):
                self.chess.promouvoir(pos, c)
                popup.destroy()
                self.chess.switchPlayer()
                self.chess.set_selected(None)
                self.mouvements_valides = []
                self.dessiner()
                self.verifier_fin()
            btn = tk.Button(frame, text=nom, width=8, font=("Arial", 11), command=choisir)
            if cle in self.images:
                btn.config(image=self.images[cle], compound=tk.TOP)
            btn.pack(side=tk.LEFT, padx=4)

    def verifier_fin(self):
        resultat = self.chess.verifier_fin()
        if resultat != None:
            self.label.config(text=resultat, fg="blue")
            self.canvas.unbind("<Button-1>")

    # calcule tous les mouvements valides pour une piece
    def calculer_mouvements(self, pos_orig):
        colonnes = Position.get_colonnes()
        valides = []
        color = self.chess.get_current_player().get_color()
        for col in colonnes:
            for row in range(1, 9):
                pos = Position(col, row)
                if self.chess.isValidMove(pos_orig, pos):
                    valides.append(pos)

        # on ajoute le roque si c'est possible
        piece = self.chess.get_board().getPiece(pos_orig)
        if isinstance(piece, King):
            row = 1 if color == 0 else 8
            if self.chess.get_board().peut_roquer_petit(color):
                valides.append(Position('g', row))
            if self.chess.get_board().peut_roquer_grand(color):
                valides.append(Position('c', row))
        return valides

    def sauvegarder(self):
        self.chess.sauvegarder()

    def charger(self):
        self.chess.charger()
        self.chess.set_selected(None)
        self.mouvements_valides = []
        self.canvas.bind("<Button-1>", self.clic)
        self.dessiner()

    def nouvelle_partie(self):
        self.chess = Chess()
        self.mouvements_valides = []
        self.canvas.bind("<Button-1>", self.clic)
        self.dessiner()

    # active ou desactive l'IA
    def toggle_ai(self):
        self.ai_active = not self.ai_active
        if self.ai_active:
            self.btn_ai.config(text="Desactiver IA")
        else:
            self.btn_ai.config(text="Activer IA")

    # fait jouer l'IA
    def jouer_ia(self):
        if self.chess.partie_terminee():
            return
        coup = self.ai.askMove(self.chess.get_board(), self.chess)
        if coup is None:
            return
        pos_orig, pos_dest = coup
        resultat = self.chess.updateBoard(pos_orig, pos_dest)
        if resultat == "promotion":
            self.chess.promouvoir(pos_dest, Queen)
        self.chess.switchPlayer()
        self.chess.set_selected(None)
        self.mouvements_valides = []
        self.dessiner()
        self.verifier_fin()
