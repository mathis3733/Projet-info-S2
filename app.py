from constantes import *
from modele import Piece, King, Queen, Rook, Bishop, Knight, Pawn, Board, Position
from joueurs import Player, AIPlayer, Chess
from graphique import (
    _make_piece_image, _build_screamer_sound, _build_screamer_surface,
    sq_to_px, px_to_sq, Button, PieceSkinLoader
)

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
