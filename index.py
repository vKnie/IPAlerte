import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
from datetime import datetime
import threading
import time

# Charger et sauvegarder les données depuis et vers le fichier JSON
def load_data():
    if os.path.exists('equipements.json'):
        try:
            with open('equipements.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            messagebox.showerror("Erreur", "Le fichier JSON est corrompu.")
            return {"equipements": []}
    else:
        return {"equipements": []}

def save_data(data):
    with open('equipements.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


# Vérification de la connectivité avec un ping
def check_ping(ip):
    try:
        command = ["ping", "-c", "1", ip] if os.name != 'nt' else ["ping", "-n", "1", ip]
        response = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        return response.returncode == 0
    except Exception:
        return False


# Mise à jour des statuts et informations de ping
def update_status_for_item(item_id, name, ip, equip):
    status = "Actif" if check_ping(ip) else "Inactif"
    last_ping_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time_since_last_ping = (datetime.now() - datetime.strptime(last_ping_time, '%Y-%m-%d %H:%M:%S')).total_seconds()
    tree.item(item_id, values=(name, ip, equip["Date"], status, f"{time_since_last_ping:.2f}s", last_ping_time, f"{equip['refresh_rate']} secondes"))
    tree.item(item_id, tags=("actif" if status == "Actif" else "inactif",))


# Lancer la mise à jour périodique pour chaque équipement
def threaded_update_status(name, item_id, ip, equip):
    def update():
        while True:
            update_status_for_item(item_id, name, ip, equip)
            time.sleep(equip["refresh_rate"])

    thread = threading.Thread(target=update, daemon=True)
    thread.start()


# Rafraîchir le Treeview avec les dernières données
def refresh_treeview():
    for item in tree.get_children():
        tree.delete(item)
    
    for item in data.get("equipements", []):
        item_id = tree.insert('', tk.END, values=(item["Nom"], item["IP"], item["Date"], "Inconnu", "N/A", "N/A", item["refresh_rate"]))
        threaded_update_status(item["Nom"], item_id, item["IP"], item)


# Ajout ou modification d'un équipement
def add_or_edit_equipement(is_edit=False, equip=None):
    def save_equipement():
        name = name_entry.get()
        ip = ip_entry.get()
        refresh_rate = int(refresh_rate_entry.get())
        
        if not name or not ip or refresh_rate < 1:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs correctement.")
            return

        if is_edit:
            equip["Nom"], equip["IP"], equip["refresh_rate"] = name, ip, refresh_rate
        else:
            new_equip = {"Nom": name, "IP": ip, "Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "refresh_rate": refresh_rate}
            data["equipements"].append(new_equip)
        
        save_data(data)
        refresh_treeview()
        equip_window.destroy()

    equip_window = tk.Toplevel(root)
    equip_window.title("Ajouter / Modifier un équipement")

    tk.Label(equip_window, text="Nom Équipement").pack()
    name_entry = tk.Entry(equip_window)
    name_entry.insert(0, equip["Nom"] if is_edit else "")
    name_entry.pack()

    tk.Label(equip_window, text="Adresse IP").pack()
    ip_entry = tk.Entry(equip_window)
    ip_entry.insert(0, equip["IP"] if is_edit else "")
    ip_entry.pack()

    tk.Label(equip_window, text="Délai de Rafraîchissement (secondes)").pack()
    refresh_rate_entry = tk.Entry(equip_window)
    refresh_rate_entry.insert(0, equip["refresh_rate"] if is_edit else "")
    refresh_rate_entry.pack()

    tk.Button(equip_window, text="Enregistrer", command=save_equipement).pack()


# Suppression d'un équipement
def delete_equipement():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Erreur", "Veuillez sélectionner un équipement à supprimer.")
        return

    item_id = selected_item[0]
    equip_name = tree.item(item_id, "values")[0]
    confirm = messagebox.askyesno("Confirmer la suppression", f"Êtes-vous sûr de vouloir supprimer l'équipement '{equip_name}' ?")
    
    if confirm:
        data["equipements"] = [e for e in data["equipements"] if e["Nom"] != equip_name]
        save_data(data)
        refresh_treeview()


# Interface graphique principale
root = tk.Tk()
root.title("Tableau des Équipements")

columns = ("Nom Équipement", "IP", "Date d'ajout", "Statut", "Temps Ping", "Dernier Ping", "Rafraîchissement")
tree = ttk.Treeview(root, columns=columns, show='headings')

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

style = ttk.Style()
style.configure("Treeview", font=("Arial", 10))
style.configure("actif", foreground="green", font=("Arial", 10, "bold"))
style.configure("inactif", foreground="red", font=("Arial", 10, "bold"))
tree.tag_configure("actif", foreground="green", font=("Arial", 10, "bold"))
tree.tag_configure("inactif", foreground="red", font=("Arial", 10, "bold"))
tree.pack(padx=10, pady=10, expand=True, fill='both')

# Menu de navigation
def create_menu():
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    equip_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Équipements", menu=equip_menu)
    equip_menu.add_command(label="Ajouter", command=lambda: add_or_edit_equipement(is_edit=False))
    equip_menu.add_command(label="Modifier", command=lambda: edit_equipement())
    equip_menu.add_command(label="Supprimer", command=delete_equipement)
    
# Modifier un équipement
def edit_equipement():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Erreur", "Veuillez sélectionner un équipement à modifier.")
        return

    item_id = selected_item[0]
    equip_name = tree.item(item_id, "values")[0]
    equip = next(e for e in data["equipements"] if e["Nom"] == equip_name)
    add_or_edit_equipement(is_edit=True, equip=equip)


create_menu()

data = load_data()
refresh_treeview()

# Lancer l'interface graphique
root.mainloop()