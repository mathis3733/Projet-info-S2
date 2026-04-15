
White = 0
Black = 1


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def askMove(self):
        while True:
            move = input(f"{self.name} ({'White' if self.color == White else 'Black'}), enter your move (e.g. 'Nb1 Nc3'): ")
            if self.validate_move(move):
                return move
            else:
                print("Invalid move format. Please try again.")

    def validate_move(self, move):
        parts = move.strip().split  
        
            
