import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import csv

# =========================================
# Lecture joueurs depuis fichier CSV tabulé Pronote
# =========================================
def lire_joueurs(fichier):
    joueurs = []
    try:
        with open(fichier, newline="", encoding="utf-8") as f:
            lecteur = csv.DictReader(f, delimiter="\t")
            for ligne in lecteur:
                nom = ligne.get("Nom", "").strip()
                prenom = ligne.get("Prénom", "").strip()
                if nom and prenom:
                    joueurs.append({
                        "nom": nom,
                        "prenom": prenom,
                        "points": 0,
                        "niveau": None
                    })
    except Exception as e:
        messagebox.showerror("Erreur import", f"Impossible de lire le fichier : {e}")
    return joueurs

# =========================================
# Application
# =========================================
class TournoiApp:

    def __init__(self, root):
        self.root = root
        self.root.title("🏆 Gestionnaire Tournoi PRO")
        self.root.geometry("1300x800")

        self.joueurs = []
        self.actifs = []
        self.vaincus = []
        self.anciens_arbitres = []
        self.tour = 1

        # ---- Paramètres affichage tables ----
        self.nb_tables_par_ligne = 5

        # ---- Menu ----
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        tournoi_menu = tk.Menu(self.menu_bar, tearoff=0)
        tournoi_menu.add_command(label="Recommencer le tournoi", command=self.recommencer)
        tournoi_menu.add_command(label="Changer nombre de tables par ligne", command=self.demander_configuration)
        tournoi_menu.add_command(label="Exporter résultats", command=self.export_csv)  # Nouveau bouton
        self.menu_bar.add_cascade(label="Tournoi", menu=tournoi_menu)

        # ---- Frame principale ----
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(fill="both", expand=True)

        # ---- Titre ----
        self.title = ttk.Label(self.main_frame,
                               text="Tournoi Élimination Directe",
                               font=("Helvetica", 24, "bold"))
        self.title.pack(pady=20)

        # ---- Boutons import / lancer tournoi ----
        self.btn_import = ttk.Button(self.main_frame, text="Importer Fichier Pronote", command=self.importer_joueurs)
        self.btn_import.pack(pady=5)

        self.btn_start = ttk.Button(self.main_frame, text="Lancer le tournoi", command=self.generer_tour, state="disabled")
        self.btn_start.pack(pady=5)

        # ---- Frame scrollable pour les tables avec scroll horizontal et vertical ----
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, borderwidth=0)
        self.scrollbar_v = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar_h = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)

        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_v.set, xscrollcommand=self.scrollbar_h.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        self.scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # ---- Bouton tour suivant ----
        self.next_button = ttk.Button(self.main_frame,
                                      text="Tour suivant",
                                      command=self.tour_suivant,
                                      state="disabled")
        self.next_button.pack(pady=20)

    # =========================================
    # Import des joueurs
    # =========================================
    def importer_joueurs(self):
        fichier = filedialog.askopenfilename(filetypes=[("CSV Tabulé", "*.csv")])
        if not fichier:
            return

        self.joueurs = lire_joueurs(fichier)
        self.actifs = self.joueurs.copy()
        self.vaincus = []
        self.anciens_arbitres = []
        self.tour = 1

        if self.joueurs:
            messagebox.showinfo("Import réussi", f"{len(self.joueurs)} joueurs importés !")
            self.btn_start.config(state="normal")
        else:
            messagebox.showwarning("Import vide", "Aucun joueur valide trouvé dans le fichier.")

    # =========================================
    # Demander configuration avant tournoi
    # =========================================
    def demander_configuration(self):
        fen = tk.Toplevel(self.root)
        fen.title("Configuration Affichage des Tables")
        fen.geometry("250x150")

        tk.Label(fen, text="Nombre de tables par ligne").pack(pady=5)
        entry_col = tk.Entry(fen)
        entry_col.insert(0, str(self.nb_tables_par_ligne))
        entry_col.pack(pady=5)

        def valider():
            try:
                self.nb_tables_par_ligne = int(entry_col.get())
            except ValueError:
                messagebox.showerror("Erreur", "Entrez un nombre valide")
                return
            fen.destroy()
            if self.actifs:
                self.generer_tour()

        tk.Button(fen, text="Valider", command=valider).pack(pady=10)

    # =========================================
    # Recommencer le tournoi
    # =========================================
    def recommencer(self):
        self.actifs = self.joueurs.copy()
        self.vaincus = []
        self.anciens_arbitres = []
        self.tour = 1
        self.next_button.config(state="disabled")
        self.generer_tour()

    # =========================================
    # Génération tour
    # =========================================
    def generer_tour(self):
        if len(self.actifs) == 1:
            self.actifs[0]["niveau"] = "vainqueur"
            self.calcul_points()
            self.afficher_classement()
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        random.shuffle(self.actifs)
        self.trinomes = []
        self.match_results = {}
        self.boutons_tables = {}
        joueurs_disponibles = self.actifs.copy()

        # Attribution arbitres
        arbitres = []
        if self.tour == 1:
            nb_matchs = len(joueurs_disponibles) // 3
            for _ in range(nb_matchs):
                arbitres.append(joueurs_disponibles.pop())
        else:
            arbitres = self.vaincus.copy()
            while len(arbitres) < len(joueurs_disponibles)//2 and self.anciens_arbitres:
                arbitres.append(self.anciens_arbitres.pop())

        self.vaincus = []

        # Création des trinomes
        i = 0
        while i + 1 < len(joueurs_disponibles):
            j1 = joueurs_disponibles[i]
            j2 = joueurs_disponibles[i+1]
            arbitre = arbitres.pop() if arbitres else None
            self.trinomes.append((j1, j2, arbitre))
            i += 2

        # Gestion joueur seul
        if i < len(joueurs_disponibles):
            j1 = joueurs_disponibles[i]
            j2 = None
            arbitre = arbitres.pop() if arbitres else None
            self.trinomes.append((j1, j2, arbitre))

        # Affichage tables
        for index, (j1, j2, arbitre) in enumerate(self.trinomes):
            frame = tk.LabelFrame(self.scrollable_frame, text=f"Table {index+1}", padx=15, pady=15)
            frame.grid(row=index // self.nb_tables_par_ligne,
                       column=index % self.nb_tables_par_ligne,
                       padx=20, pady=20, sticky="n")

            texte_arbitre = f"Arbitre : {arbitre['prenom']} {arbitre['nom']}" if arbitre else "Arbitre : Prof"
            tk.Label(frame, text=texte_arbitre, font=("Helvetica", 11)).pack(pady=5)

            btn1 = tk.Button(frame, text=f"{j1['prenom']} {j1['nom']}", width=20, height=2)
            btn1.pack(pady=5)

            if j2:
                btn2 = tk.Button(frame, text=f"{j2['prenom']} {j2['nom']}", width=20, height=2)
                btn2.pack(pady=5)
                btn1.config(command=lambda i=index: self.selectionner(i, 1))
                btn2.config(command=lambda i=index: self.selectionner(i, 2))
            else:
                # Cas joueur seul vs arbitre
                btn2 = None
                btn1.config(command=lambda i=index: self.selectionner_joueur_vs_arbitre(i))

            self.boutons_tables[index] = (btn1, btn2)

        self.next_button.config(state="disabled")

    # =========================================
    # Sélection réversible
    # =========================================
    def selectionner(self, index, winner):
        j1, j2, arbitre = self.trinomes[index]
        btn1, btn2 = self.boutons_tables[index]

        if btn1: btn1.config(bg="SystemButtonFace", fg="black")
        if btn2: btn2.config(bg="SystemButtonFace", fg="black")

        if winner == 1:
            gagnant = j1
            perdant = j2
            btn1.config(bg="#4CAF50", fg="white")
        else:
            gagnant = j2
            perdant = j1
            btn2.config(bg="#4CAF50", fg="white")

        self.match_results[index] = (gagnant, perdant)

        if len(self.match_results) == len(self.trinomes):
            self.next_button.config(state="normal")
        else:
            self.next_button.config(state="disabled")

    # =========================================
    # Joueur seul vs arbitre
    # =========================================
    def selectionner_joueur_vs_arbitre(self, index):
        j1, j2, arbitre = self.trinomes[index]
        prof = {"prenom": "Prof", "nom": ""} if arbitre is None else arbitre

        res = messagebox.askyesno("Match spécial",
                                  f"{j1['prenom']} {j1['nom']} joue contre {prof['prenom']}\nCliquez Oui si le joueur gagne, Non s'il perd.")

        if res:  # joueur gagne
            gagnant = j1
            perdant = None
            self.boutons_tables[index][0].config(bg="#4CAF50", fg="white")
        else:      # joueur perd
            gagnant = None
            perdant = j1
            self.boutons_tables[index][0].config(bg="#F44336", fg="white")  # rouge pour éliminé

        self.match_results[index] = (gagnant, perdant)

        if len(self.match_results) == len(self.trinomes):
            self.next_button.config(state="normal")
        else:
            self.next_button.config(state="disabled")

    # =========================================
    # Tour suivant
    # =========================================
    def tour_suivant(self):
        self.vainqueurs_tour = []
        self.vaincus = []

        for index in self.match_results:
            gagnant, perdant = self.match_results[index]
            if gagnant:
                self.vainqueurs_tour.append(gagnant)
            if perdant:
                self.vaincus.append(perdant)
                perdant["niveau"] = f"Tour {self.tour}"

        for _, _, arbitre in self.trinomes:
            if arbitre:
                self.anciens_arbitres.append(arbitre)

        self.actifs = self.vainqueurs_tour
        self.tour += 1
        self.next_button.config(state="disabled")
        self.generer_tour()

    # =========================================
    # Calcul points corrigé
    # =========================================
    def calcul_points(self):
        for j in self.joueurs:
            if j["niveau"] == "vainqueur":
                j["points"] = 20
            elif j["niveau"] == f"Tour {self.tour-1}":
                j["points"] = 18
            elif j["niveau"] == f"Tour {self.tour-2}":
                j["points"] = 16
            elif j["niveau"] == f"Tour {self.tour-3}":
                j["points"] = 14
            else:
                j["points"] = 10

    # =========================================
    # Classement final
    # =========================================
    def afficher_classement(self):
        fenetre = tk.Toplevel(self.root)
        fenetre.title("Classement Final")
        fenetre.geometry("650x550")

        tk.Label(fenetre, text="🏆 Classement Final", font=("Helvetica", 18, "bold")).pack(pady=20)

        tree = ttk.Treeview(fenetre, columns=("Nom", "Prénom", "Points"), show="headings")
        tree.heading("Nom", text="Nom")
        tree.heading("Prénom", text="Prénom")
        tree.heading("Points", text="Points")

        joueurs_sorted = sorted(self.joueurs, key=lambda x: x["nom"])
        for j in joueurs_sorted:
            tree.insert("", "end", values=(j["nom"], j["prenom"], j["points"]))

        tree.pack(expand=True)

        tk.Button(fenetre, text="Exporter CSV", command=self.export_csv).pack(pady=10)

    # =========================================
    # Export CSV
    # =========================================
    def export_csv(self):
        fichier = filedialog.asksaveasfilename(defaultextension=".csv",
                                               filetypes=[("CSV", "*.csv")])
        if not fichier:
            return

        with open(fichier, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Nom", "Prénom", "Points"])
            for j in sorted(self.joueurs, key=lambda x: x["nom"]):
                writer.writerow([j["nom"], j["prenom"], j["points"]])

        messagebox.showinfo("Export réussi", f"Fichier {fichier} créé !")


# =========================================
# Lancement
# =========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = TournoiApp(root)
    root.mainloop()
