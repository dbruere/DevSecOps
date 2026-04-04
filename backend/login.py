from flask import render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import hashlib
from flask_jwt_extended import create_access_token, set_access_cookies


def sha256_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


# checker le user et le pass


def check_user(db, login, password):
    query = text(
        "SELECT id, nom, prenom, login, password, role, classes, matiere FROM users WHERE login=:login AND password=:password LIMIT 1"
    )
    result = db.session.execute(query, {"login": login, "password": password})

    user_row = result.fetchone()

    if user_row:
        return True, user_row
    return False, None


def login(db):
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form.get("username")
        password = sha256_hash(request.form.get("password"))

        verif, user_row = check_user(db, username, password)

        if verif:
            claims_supplementaires = {
                "id": user_row.id,
                "role": user_row.role,
                "nom": user_row.nom,
                "prenom": user_row.prenom,
                "classes": user_row.classes,
                "matiere": user_row.matiere,
            }

            token = create_access_token(
                identity=username, additional_claims=claims_supplementaires
            )

            resp = make_response(redirect("/"))
            set_access_cookies(resp, token)

            return resp
        else:
            return "Nom d'utilisateur ou mot de passe incorrecte"

    else:
        return "Méthode non autorisée"
