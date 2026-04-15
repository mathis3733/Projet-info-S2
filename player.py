
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

        if len(parts) !=2:
            return False
        
        origin = parts[0]
        destination = parts[1]

        if len(origin) < 3 or len(destination) < 3:
            