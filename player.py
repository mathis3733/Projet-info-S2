x = 5

class player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
    
    def askmove(self):
        while True:
            move = input(f"{self.name} ({self.color}), enter your move (e.g. 'e2 e4'): ")
            if self.validate_move(move):
                return move
            else:
                print("Invalid move format. Please try again.")