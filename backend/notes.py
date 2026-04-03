from flask import render_template, request, redirect, url_for
from flask_jwt_extended import get_jwt_identity, get_jwt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def notes(db):

    current_username = get_jwt_identity()
    mes_claims = get_jwt()
    user_id = mes_claims.get("id")
    role = mes_claims.get("role")
    nom = mes_claims.get("nom")
    prenom = mes_claims.get("prenom")
    user = prenom + " " + nom
    classes = mes_claims.get("classes")
    matiere = mes_claims.get("matiere")

    if request.method == 'POST':
        if role != 'professeur':
            abort(403)
        query_insert = text("""
            INSERT INTO notes (etudiant_id, professeur_id, matiere, valeur, created_at) 
            VALUES (:etu, :prof, :mat, :val, CURRENT_TIMESTAMP)
        """)
        db.session.execute(query_insert, {
            "etu": request.form.get('etudiant_id'),
            "prof": user_id,
            "mat": request.form.get('matiere'),
            "val": request.form.get('valeur')
        })
        db.session.commit()
        return redirect(url_for('notes_route'))

    if role == 'etudiant':
        query = text("""
            SELECT n.matiere, n.valeur, DATE_FORMAT(n.created_at, '%d/%m/%Y') AS date_formatee, 
                   u.prenom AS prof_prenom, u.nom AS prof_nom
            FROM notes n
            JOIN users u ON n.professeur_id = u.id
            WHERE n.etudiant_id = :uid
            ORDER BY n.created_at DESC
        """)
        notes = db.session.execute(query, {"uid": user_id}).mappings().all()
    else:
        query = text("""
            SELECT n.matiere, n.valeur, DATE_FORMAT(n.created_at, '%d/%m/%Y') AS date_formatee, 
                   u.prenom AS etudiant_prenom, u.nom AS etudiant_nom
            FROM notes n
            JOIN users u ON n.etudiant_id = u.id
            WHERE n.professeur_id = :uid
            ORDER BY n.created_at DESC
        """)
        notes = db.session.execute(query, {"uid": user_id}).mappings().all()

    # On s'assure que prof_classes ne vaut pas "None" s'il n'a pas de classe assignée
    prof_classes_str = classes if classes else ""
    
    # FIND_IN_SET(A, B) cherche si la valeur A de l'étudiant se trouve dans la liste B du prof !
    query_etu = text("""
        SELECT id, nom, prenom 
        FROM users 
        WHERE role = 'etudiant' 
        AND FIND_IN_SET(classes, :prof_classes) > 0
    """)
    etudiants = db.session.execute(query_etu, {"prof_classes": prof_classes_str}).mappings().all()

    return render_template('note.html', notes=notes, role=role, etudiants=etudiants, matieres=matiere)