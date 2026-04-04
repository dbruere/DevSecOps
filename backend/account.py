from flask import render_template, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import hashlib


def account(db):

    current_username = get_jwt_identity()
    mes_claims = get_jwt()
    role = mes_claims.get("role")
    nom = mes_claims.get("nom")
    prenom = mes_claims.get("prenom")
    user = prenom + " " + nom
    classes = mes_claims.get("classes")
    matiere = mes_claims.get("matiere")

    sql_all_users = text(
        "SELECT nom, prenom, login, classes, matiere, role FROM users"
    )
    result = db.session.execute(sql_all_users)
    all_users = result.fetchall()  # On récupère toutes les lignes

    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        role = request.form.get("role")
        password = hashlib.sha256(
            (request.form.get("password")).encode()
        ).hexdigest()

        # On récupère toutes les classes cochées dans un tableau Python : ["1",
        # "3"]
        classes_array = request.form.getlist("classes")
        # On les rejoint avec des virgules (donnera "1,3"). S'il n'y a rien, on
        # met None.
        classes_str = ",".join(classes_array) if classes_array else None

        # On récupère la matière uniquement si c'est un professeur
        matiere = request.form.get("matiere") if role == "professeur" else None

        if nom == "" or prenom == "" or role == "" or password == "":
            return render_template(
                "account.html", error="Veuillez remplir tous les champs"
            )
        elif role not in ["admin", "professeur", "etudiant"]:
            return render_template("account.html", error="Rôle invalide")
        else:
            if prenom and nom and role and password:
                login = prenom[0].lower() + nom.lower()

                sql_query = text("""
                    INSERT INTO users (nom, prenom, login, password, role, classes, matiere)
                    VALUES (:nom, :prenom, :login, :password, :role, :classes, :matiere)
                    """)

                try:

                    db.session.execute(
                        sql_query,
                        {
                            "nom": nom,
                            "prenom": prenom,
                            "login": login,
                            "password": password,
                            "role": role,
                            "classes": classes_str,
                            "matiere": matiere,
                        },
                    )

                    db.session.commit()

                    return render_template(
                        "account.html",
                        success=f"Compte {login} créé !",
                        admin=user,
                        users_list=all_users,
                    )
                except Exception as e:
                    db.session.rollback()
                    return render_template(
                        "account.html",
                        error=f"Erreur DB : {str(e)}",
                        admin=user,
                        users_list=all_users,
                    )
            else:
                return render_template(
                    "account.html",
                    error="Veuillez remplir tous les champs",
                    admin=user,
                    users_list=all_users,
                )

    if request.method == "GET":

        return render_template(
            "account.html", admin=user, users_list=all_users
        )
