import tkinter as tk


class PayToWin:
    def __init__(self, chess, app):
        self.chess = chess
        self.app = app
        self.prix = 100

    def acheter_victoire(self):
        popup = tk.Toplevel()
        popup.title("Pay to Win")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="PAY TO WIN", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(popup, text="Gagnez instantanement pour seulement " + str(self.prix) + "euros !", font=("Arial", 11)).pack()
        tk.Label(popup, text="(offre limitee)", font=("Arial", 9), fg="gray").pack()

        self.entry = tk.Entry(popup, font=("Arial", 13), justify="center")
        self.entry.pack(pady=10)
        self.entry.insert(0, "Entrez " + str(self.prix))

        tk.Button(popup, text="PAYER ET GAGNER", font=("Arial", 12, "bold"), bg="green", fg="white",
                  command=lambda: self.valider(popup)).pack(pady=5)
        tk.Button(popup, text="Non merci je prefere perdre", font=("Arial", 8), fg="gray",
                  command=popup.destroy).pack(pady=2)

    def valider(self, popup):
        try:
            montant = float(self.entry.get())
            if montant >= self.prix:
                popup.destroy()
                self.chess._Chess__partie_terminee = True
                nom = self.chess.get_current_player().get_name()
                self.app._App__label.config(
                    text=nom + " a paye " + str(montant) + " euros et a gagne !", fg="green"
                )
                self.app._App__canvas.unbind("<Button-1>")
                self.app._App__dessiner()
            else:
                tk.Label(popup, text="Pas assez... il faut " + str(self.prix) + " euros minimum !", fg="red").pack()
        except ValueError:
            tk.Label(popup, text="Mettez un vrai montant !", fg="red").pack()
