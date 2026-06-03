# la classe Position sert a savoir ou est une piece sur le plateau
class Position:
    def __init__(self, column, row):
        self.column = column  # la colonne ex: 'a', 'b'...
        self.row = row        # la ligne ex: 1, 2...

    def get_column(self):
        return self.column

    def get_row(self):
        return self.row

    # retourne toutes les colonnes du plateau
    def get_colonnes():
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    def __str__(self):
        return self.column + str(self.row)

    # pour comparer deux positions
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.column == other.get_column() and self.row == other.get_row()
