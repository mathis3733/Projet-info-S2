from abc import ABC, abstractmethod

# classe abstraite pour les pieces, toutes les pieces heritent de cette classe
class Piece(ABC):
    def __init__(self, position, color):
        self.position = position
        self.color = color  # 0 = blanc, 1 = noir

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def get_color(self):
        return self.color

    # methode abstraite, chaque piece doit definir comment elle bouge
    @abstractmethod
    def isValidMove(self, newPosition, board):
        pass

    @abstractmethod
    def __str__(self):
        pass
