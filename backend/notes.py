from flask import render_template, request, redirect, url_for, abort
from flask_jwt_extended import get_jwt
from sqlalchemy import text


def notes(db):

    # test current_username = get_jwt_identity()
    mes_claims = get_jwt()
    user_id = mes_claims.get("id")
    role = mes_claims.get("role")
    classes = mes_claims.get("classes")
    matiere = mes_claims.get("matiere")

    if request.method == "POST":
        if role not in ["professeur", "admin"]:
            abort(403)

        action = request.form.get("action")

        if action == "edit":
            if role != "admin":
                abort(403)
            query_update = text("""
                UPDATE notes SET valeur = :val
                WHERE id = :nid
            """)
            db.session.execute(
                query_update,
                {
                    "val": request.form.get("nouvelle_valeur"),
                    "nid": request.form.get("note_id"),
                },
            )
        elif action == "delete":
            if role != "admin":
                abort(403)
            query_delete = text("""
                DELETE FROM notes WHERE id = :nid
            """)
            db.session.execute(
                query_delete, {"nid": request.form.get("note_id")}
            )
        else:
            query_insert = text("""
                INSERT INTO notes (etudiant_id, professeur_id, matiere, valeur, created_at)
                VALUES (:etu, :prof, :mat, :val, CURRENT_TIMESTAMP)
            """)
            db.session.execute(
                query_insert,
                {
                    "etu": request.form.get("etudiant_id"),
                    "prof": user_id,
                    "mat": request.form.get("matiere"),
                    "val": request.form.get("valeur"),
                },
            )

        db.session.commit()
        return redirect(url_for("notes_route"))

    if role == "etudiant":
        query = text("""
            SELECT n.id, n.matiere, n.valeur, DATE_FORMAT(n.created_at, '%d/%m/%Y') AS date_formatee,
                   u.prenom AS prof_prenom, u.nom AS prof_nom
            FROM notes n
            JOIN users u ON n.professeur_id = u.id
            WHERE n.etudiant_id = :uid
            ORDER BY n.created_at DESC
        """)
        notes = db.session.execute(query, {"uid": user_id}).mappings().all()
    elif role == "admin":
        query = text("""
            SELECT n.id, n.matiere, n.valeur, DATE_FORMAT(n.created_at, '%d/%m/%Y') AS date_formatee,
                   u.prenom AS etudiant_prenom, u.nom AS etudiant_nom
            FROM notes n
            JOIN users u ON n.etudiant_id = u.id
            ORDER BY n.created_at DESC
        """)
        notes = db.session.execute(query).mappings().all()
    else:
        query = text("""
            SELECT n.id, n.matiere, n.valeur, DATE_FORMAT(n.created_at, '%d/%m/%Y') AS date_formatee,
                   u.prenom AS etudiant_prenom, u.nom AS etudiant_nom
            FROM notes n
            JOIN users u ON n.etudiant_id = u.id
            WHERE n.professeur_id = :uid
            ORDER BY n.created_at DESC
        """)
        notes = db.session.execute(query, {"uid": user_id}).mappings().all()

    # On s'assure que prof_classes ne vaut pas "None" s'il n'a pas de classe
    # assignée
    prof_classes_str = classes if classes else ""

    # FIND_IN_SET(A, B) cherche si la valeur A de l'étudiant se trouve dans la
    # liste B du prof !
    query_etu = text("""
        SELECT id, nom, prenom
        FROM users
        WHERE role = 'etudiant'
        AND FIND_IN_SET(classes, :prof_classes) > 0
    """)
    etudiants = (
        db.session.execute(query_etu, {"prof_classes": prof_classes_str})
        .mappings()
        .all()
    )

    return render_template(
        "note.html",
        notes=notes,
        role=role,
        etudiants=etudiants,
        matieres=matiere,
    )
