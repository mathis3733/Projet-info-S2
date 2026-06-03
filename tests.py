import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from echecs import Position, Board, King, Queen, Bishop, Knight, Rook, Pawn


class TestPosition(unittest.TestCase):
    def test_str(self):
        p = Position('e', 4)
        self.assertEqual(str(p), 'e4')

    def test_egalite(self):
        self.assertEqual(Position('a', 1), Position('a', 1))

    def test_inegalite(self):
        self.assertNotEqual(Position('a', 1), Position('b', 1))


class TestPion(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_avance_une_case(self):
        p = self.board.getPiece(Position('e', 2))
        self.assertTrue(p.isValidMove(Position('e', 3), self.board))

    def test_avance_deux_cases_depart(self):
        p = self.board.getPiece(Position('e', 2))
        self.assertTrue(p.isValidMove(Position('e', 4), self.board))

    def test_ne_peut_pas_avancer_trois_cases(self):
        p = self.board.getPiece(Position('e', 2))
        self.assertFalse(p.isValidMove(Position('e', 5), self.board))

    def test_bloque_par_piece(self):
        p = self.board.getPiece(Position('e', 2))
        self.assertFalse(p.isValidMove(Position('e', 2), self.board))

    def test_ne_peut_pas_reculer(self):
        p = self.board.getPiece(Position('e', 7))
        self.assertFalse(p.isValidMove(Position('e', 8), self.board))


class TestCavalier(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_mouvement_valide_L(self):
        p = self.board.getPiece(Position('b', 1))
        self.assertTrue(p.isValidMove(Position('c', 3), self.board))

    def test_mouvement_valide_L2(self):
        p = self.board.getPiece(Position('b', 1))
        self.assertTrue(p.isValidMove(Position('a', 3), self.board))

    def test_mouvement_invalide(self):
        p = self.board.getPiece(Position('b', 1))
        self.assertFalse(p.isValidMove(Position('b', 3), self.board))

    def test_saute_par_dessus(self):
        p = self.board.getPiece(Position('b', 1))
        self.assertTrue(p.isValidMove(Position('c', 3), self.board))


class TestTour(unittest.TestCase):
    def setUp(self):
        self.board = Board.__new__(Board)
        self.board._Board__pieces = []
        self.board._Board__en_passant = None
        self.tour = Rook(Position('d', 4), 0)
        self.board._Board__pieces.append(self.tour)

    def test_deplacement_horizontal(self):
        self.assertTrue(self.tour.isValidMove(Position('h', 4), self.board))

    def test_deplacement_vertical(self):
        self.assertTrue(self.tour.isValidMove(Position('d', 8), self.board))

    def test_deplacement_diagonal_invalide(self):
        self.assertFalse(self.tour.isValidMove(Position('e', 5), self.board))

    def test_bloquee_par_piece(self):
        self.board._Board__pieces.append(Pawn(Position('d', 6), 0))
        self.assertFalse(self.tour.isValidMove(Position('d', 8), self.board))


class TestFou(unittest.TestCase):
    def setUp(self):
        self.board = Board.__new__(Board)
        self.board._Board__pieces = []
        self.board._Board__en_passant = None
        self.fou = Bishop(Position('d', 4), 0)
        self.board._Board__pieces.append(self.fou)

    def test_deplacement_diagonal(self):
        self.assertTrue(self.fou.isValidMove(Position('g', 7), self.board))

    def test_deplacement_droit_invalide(self):
        self.assertFalse(self.fou.isValidMove(Position('d', 7), self.board))

    def test_bloque_par_piece(self):
        self.board._Board__pieces.append(Pawn(Position('f', 6), 0))
        self.assertFalse(self.fou.isValidMove(Position('g', 7), self.board))


class TestRoi(unittest.TestCase):
    def setUp(self):
        self.board = Board.__new__(Board)
        self.board._Board__pieces = []
        self.board._Board__en_passant = None
        self.roi = King(Position('e', 4), 0)
        self.board._Board__pieces.append(self.roi)

    def test_deplacement_une_case(self):
        self.assertTrue(self.roi.isValidMove(Position('e', 5), self.board))

    def test_deplacement_deux_cases_invalide(self):
        self.assertFalse(self.roi.isValidMove(Position('e', 6), self.board))

    def test_deplacement_diagonal(self):
        self.assertTrue(self.roi.isValidMove(Position('f', 5), self.board))


class TestReine(unittest.TestCase):
    def setUp(self):
        self.board = Board.__new__(Board)
        self.board._Board__pieces = []
        self.board._Board__en_passant = None
        self.reine = Queen(Position('d', 4), 0)
        self.board._Board__pieces.append(self.reine)

    def test_deplacement_horizontal(self):
        self.assertTrue(self.reine.isValidMove(Position('h', 4), self.board))

    def test_deplacement_diagonal(self):
        self.assertTrue(self.reine.isValidMove(Position('g', 7), self.board))

    def test_deplacement_invalide(self):
        self.assertFalse(self.reine.isValidMove(Position('e', 6), self.board))


if __name__ == '__main__':
    unittest.main()
