from flask import Flask, render_template, request, redirect, session
import pymysql

app = Flask(__name__)
app.secret_key = "gisele"  # Clé secrète pour gérer la session

# Connexion à la base de données MySQL
db = pymysql.connect(
    host="localhost",
    user="root",
    database="gisele"
)

# Route de la page d'accueil
@app.route("/", methods=["GET", "POST"])
def home():
    cursor = db.cursor()  # Création du curseur à l'intérieur de la fonction home
    if request.method == "POST":
        full_name = request.form["full_name"]
        cursor.execute("SELECT full_name FROM utilisateurs WHERE full_name = %s", (full_name,))
        result = cursor.fetchone()
        if result:
            session["full_name"] = full_name
            return redirect("/table")
        else:
            return "Nom d'utilisateur incorrect. Veuillez réessayer."
    return render_template("accueil.html")

# Route de la page de la table
@app.route("/table", methods=["GET", "POST"])
def table():
    if "full_name" not in session:
        return redirect("/")  # Rediriger vers la page d'accueil si l'utilisateur n'est pas connecté
    full_name = session["full_name"]
    is_admin = True if full_name == "Wembalola.Eleonore" else False
    cursor = db.cursor()  # Création du curseur à l'intérieur de la fonction table

    # Récupérer les données du tableau depuis la base de données
    cursor.execute("SELECT row, col, full_name FROM table_data")
    rows = cursor.fetchall()
    table_data = {f"cell-{row[0]}-{row[1]}": row[2] for row in rows}

    # Traitement des modifications dans les cellules
    if request.method == "POST":
        row = int(request.form["row"])
        col = int(request.form["col"])
        text = request.form.get("text", "")  # Récupérer le texte du formulaire

        clicked_cell = f"cell-{row}-{col}"
        if is_admin:
            # L'admin peut écrire du texte dans toutes les cases
            table_data[clicked_cell] = text
            cursor.execute("INSERT INTO table_data (row, col, full_name) VALUES (%s, %s, %s) "
                           "ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)",
                           (row, col, text))
        else:
            # Pour les autres utilisateurs, gérer les clics sur les lignes 2 et 3
            current_name = table_data.get(clicked_cell)
            if current_name and current_name == full_name:
                if text:  # Si l'utilisateur modifie le texte, mettre à jour la ligne dans la base de données
                    cursor.execute("UPDATE table_data SET full_name = %s WHERE row = %s AND col = %s",
                                   (text, row, col))
                else:  # Sinon, supprimer la ligne de la base de données
                    cursor.execute("DELETE FROM table_data WHERE row = %s AND col = %s", (row, col))
                table_data[clicked_cell] = text
            else:
                table_data[clicked_cell] = full_name
                cursor.execute("INSERT INTO table_data (row, col, full_name) VALUES (%s, %s, %s)",
                               (row, col, full_name))
        db.commit()

    return render_template("table.html", full_name=full_name, is_admin=is_admin, table_data=table_data)


if __name__ == "__main__":
    app.run(debug=True)
