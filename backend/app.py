from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlsplit
from functools import wraps
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
# Une vraie clé secrète est nécessaire pour les sessions (utiliser variables d'environnement en prod)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-devsecops")

# Connexion à MySQL via Docker (nom du service 'db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://test:test@127.0.0.1:3306/intranet')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODÈLES DB =================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    nom = db.Column(db.String(50), nullable=True, default="Doe")
    prenom = db.Column(db.String(50), nullable=True, default="John")
    classe = db.Column(db.String(50), nullable=True, default="1")
    matiere = db.Column(db.String(100), nullable=True)

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matiere = db.Column(db.String(100), nullable=False)
    valeur = db.Column(db.Float, nullable=False)
    date_ajout = db.Column(db.DateTime, server_default=db.func.now())

class Cours(db.Model):
    __tablename__ = 'cours'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    professeur = db.Column(db.String(100), nullable=True)
    start = db.Column(db.String(50), nullable=False)
    end = db.Column(db.String(50), nullable=False)
    classe = db.Column(db.String(50), nullable=True)

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_limite = db.Column(db.String(50), nullable=True)
    classe = db.Column(db.String(50), nullable=False)
    professeur = db.Column(db.String(100), nullable=False)

# ================= INITIALISATION DB =================
with app.app_context():
    db.create_all()
    # Création des utilisateurs par défaut si la table est vide
    if not User.query.first():
        db.session.add(User(login="admin", password=generate_password_hash("admin123", method="scrypt"), role="admin", prenom="Super", nom="Admin"))
        db.session.add(User(login="prof", password=generate_password_hash("prof123", method="scrypt"), role="professeur", prenom="Jean", nom="Prof"))
        db.session.add(User(login="eleve", password=generate_password_hash("eleve123", method="scrypt"), role="etudiant", prenom="Alice", nom="Eleve"))
        db.session.commit()
        print("Utilisateurs de test créés.")

# ================= DÉCORATEURS RBAC =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page", "danger")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Vérifie si l'utilisateur possède l'un des rôles demandés."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                abort(403) # Interdit selon Cahier des Charges
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ================= ROUTES =================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('accueil'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(login=username).first()
        
        # Sécurité : bcrypt validation
        if user and check_password_hash(user.password, password):
            # Session handling
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.login
            session['user_role'] = user.role
            
            flash("Connexion réussie", "success")
            
            # Gestion basique du next_url pour rediriger au bon endroit
            next_url = request.args.get('next')
            if not next_url or urlsplit(next_url).netloc != '':
                return redirect(url_for('accueil'))
            return redirect(next_url)
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté", "info")
    return redirect(url_for('login'))

from datetime import datetime

@app.route('/accueil')
@login_required
def accueil():
    recent_notes = []
    if session.get('user_role') == 'etudiant':
        # Notes pour cet étudiant
        notes_query = Note.query.filter_by(etudiant_id=session.get('user_id')).order_by(Note.date_ajout.desc()).limit(3).all()
        # EDT : Restreindre par classe pour l'élève
        user = User.query.get(session.get('user_id'))
        user_c = user.classe if user and user.classe else '1'
        cours_query = Cours.query.filter_by(classe=user_c).all()
    else:
        # Top 3 de toutes les notes pour admin/prof
        notes_query = Note.query.order_by(Note.date_ajout.desc()).limit(3).all()
        cours_query = Cours.query.all()

    for n in notes_query:
        etu = User.query.get(n.etudiant_id)
        recent_notes.append({
            'matiere': n.matiere,
            'valeur': n.valeur,
            'etudiant_nom': f"{etu.prenom} {etu.nom}" if etu else 'N/A',
            'date_formatee': n.date_ajout.strftime("%d/%m/%Y") if n.date_ajout else "N/A"
        })

    # Filtrer les cours pour "aujourd'hui"
    actual_today = datetime.now().strftime('%Y-%m-%d')
    cours_jour = [c for c in cours_query if c.start.startswith(actual_today)]
        
    cours_jour = sorted(cours_jour, key=lambda c: c.start)

    import random
    liste_actualites = [
        {"type": "urgence", "titre": "Fermeture du serveur de test", "desc": "Le serveur sera indisponible aujourd'hui de 13h à 14h pour une mise à jour.", "date": "Aujourd'hui, 09:00"},
        {"type": "info", "titre": "Nouveau TP en ligne", "desc": "Les supports de cours d'Administration Linux avancée sont maintenant disponibles.", "date": "Hier, 16:30"},
        {"type": "info", "titre": "Réunion des délégués", "desc": "Rappel : réunion demain à 10h en salle B201.", "date": "Aujourd'hui, 08:15"},
        {"type": "urgence", "titre": "Alerte de Sécurité", "desc": "Merci de mettre à jour les mots de passe de vos sessions ENT.", "date": "À l'instant"},
        {"type": "info", "titre": "Conférence DevSecOps", "desc": "L'inscription à la conférence de la semaine prochaine est ouverte.", "date": "Hier, 14:00"}
    ]
    actus_aleatoires = random.sample(liste_actualites, 2)

    return render_template('accueil.html', role=session.get('user_role'), username=session.get('username'), recent_notes=recent_notes, cours_jour=cours_jour, actus=actus_aleatoires)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_users():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            role = request.form.get('role')
            hashed_pw = generate_password_hash(request.form.get('password'), method="scrypt")
            
            classe = request.form.get('classe') if role == 'etudiant' else '0'
            matiere = request.form.get('matiere') if role == 'professeur' else None

            new_user = User(
                login=request.form.get('login'),
                password=hashed_pw,
                role=role,
                prenom=request.form.get('prenom'),
                nom=request.form.get('nom'),
                classe=classe,
                matiere=matiere
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Utilisateur créé avec succès", "success")
        elif action == 'edit_all':
            delete_user_id = request.form.get('delete_user')
            if delete_user_id:
                user = User.query.get(delete_user_id)
                if user and getattr(user, 'login', '') != 'admin':
                    try:
                        Note.query.filter_by(etudiant_id=user.id).delete()
                    except:
                        pass
                    db.session.delete(user)
                    db.session.commit()
                    flash('Utilisateur supprimé avec succès', 'success')
                elif user and getattr(user, 'login', '') == 'admin':
                    flash('Action non autorisée : Vous ne pouvez pas supprimer le Super Admin', 'error')
                return redirect(url_for('admin_users'))

            user_ids = request.form.getlist('user_id_list')
            for uid in user_ids:
                user = User.query.get(uid)
                if not user:
                    continue
                
                login_val = request.form.get(f'login_{uid}')
                if login_val and login_val.strip() != '':
                    if getattr(user, 'login', '') != 'admin':
                        user.login = login_val.strip()
                
                password_val = request.form.get(f'password_{uid}')
                if password_val and password_val.strip() != '':
                    user.password = generate_password_hash(password_val.strip(), method='scrypt')
                
                if getattr(user, 'login', '') != 'admin':
                    role_val = request.form.get(f'role_{uid}')
                    if role_val and role_val.strip() != '':
                        user.role = role_val.strip()
                    
                    if getattr(user, 'role', '') == 'etudiant':
                        classe_val = request.form.get(f'classe_{uid}')
                        if classe_val and classe_val.strip() != '':
                            user.classe = classe_val.strip()
                        user.matiere = None
                    elif getattr(user, 'role', '') == 'professeur':
                        matiere_val = request.form.get(f'matiere_{uid}')
                        if matiere_val and matiere_val.strip() != '':
                            user.matiere = matiere_val.strip()
                        user.classe = '0'
            
            db.session.commit()
            flash('Tous les utilisateurs ont été mis à jour avec succès', 'success')

        return redirect(url_for('admin_users'))
        
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            if session.get('user_role') == 'admin':
                note_id = request.form.get('note_id')
                note = Note.query.get(note_id)
                if note:
                    db.session.delete(note)
                    db.session.commit()
                    flash("Note supprimée avec succès", "success")
        elif action == 'edit':
            if session.get('user_role') == 'admin':
                note_id = request.form.get('note_id')
                nouvelle_valeur = request.form.get('nouvelle_valeur')
                print(f"================ EDIT RECEIVED: {note_id}, {nouvelle_valeur} ================", flush=True)
                if note_id and nouvelle_valeur:
                    note = Note.query.get(int(note_id))
                    if note:
                        try:
                            note.valeur = float(str(nouvelle_valeur).replace(',', '.'))
                            db.session.commit()
                            flash("Note modifiée avec succès", "success")
                        except ValueError:
                            flash("Valeur invalide pour la note.", "error")
        else:
            # Action classique d'ajout
            if session.get('user_role') in ['professeur', 'admin']:
                etu_id = request.form.get('etudiant_id')
                matiere = request.form.get('matiere', 'Matière par défaut')
                valeur = request.form.get('valeur')
                if etu_id and valeur:
                    try:
                        val_float = float(str(valeur).replace(',', '.'))
                        nouvelle_note = Note(etudiant_id=etu_id, matiere=matiere, valeur=val_float)
                        db.session.add(nouvelle_note)
                        db.session.commit()
                        flash("Note ajoutée avec succès", "success")
                    except ValueError:
                        flash("Valeur de note invalide", "error")

    # RBAC: Tout le monde a un accès mais différent
    # Un étudiant ne voit que ses notes, un prof ou admin voit toutes les notes (ou selon les règles précises)
    matieres = ['Sécurité des Réseaux', 'Cryptographie', 'Développement Sécurisé']
    etudiants = User.query.filter_by(role='etudiant').all()

    if session.get('user_role') == 'etudiant':
        notes_query = Note.query.filter_by(etudiant_id=session.get('user_id')).all()
    else:
        notes_query = Note.query.all()
    
    # Formatage pour le template
    notes_list = []
    for n in notes_query:
        etu = User.query.get(n.etudiant_id)
        notes_list.append({
            'id': n.id,
            'matiere': n.matiere,
            'valeur': n.valeur,
            'etudiant_prenom': etu.prenom if etu else 'N/A',
            'etudiant_nom': etu.nom if etu else 'N/A',
            'date_formatee': n.date_ajout.strftime("%d/%m/%Y") if n.date_ajout else "N/A"
        })

    return render_template('note.html', role=session.get('user_role'), matieres=matieres, etudiants=etudiants, notes=notes_list)

@app.route('/evaluations', methods=['GET', 'POST'])
@login_required
def evaluations():
    role = session.get('user_role')
    username = session.get('username')
    
    # Récupérer les classes disponibles pour les profs (à partir de tous les étudiants ou des cours existants)
    classes_disponibles = ['1', '2', '3', '4']
    
    if request.method == 'POST' and role in ['professeur', 'admin']:
        action = request.form.get('action')
        if action == 'create':
            titre = request.form.get('titre')
            description = request.form.get('description')
            date_limite = request.form.get('date_limite')
            classe = request.form.get('classe')
            nouvelle_eval = Evaluation(
                titre=titre,
                description=description,
                date_limite=date_limite,
                classe=classe,
                professeur=username
            )
            db.session.add(nouvelle_eval)
            db.session.commit()
            flash("Évaluation/Projet créé avec succès", "success")
        elif action == 'delete':
            eval_id = request.form.get('eval_id')
            evaluation = Evaluation.query.get(eval_id)
            if evaluation and (role == 'admin' or evaluation.professeur == username):
                db.session.delete(evaluation)
                db.session.commit()
                flash("Évaluation/Projet supprimé avec succès", "success")
        return redirect(url_for('evaluations'))

    if role == 'etudiant':
        user = User.query.get(session.get('user_id'))
        user_c = user.classe if user and user.classe else '1'
        evals_query = Evaluation.query.filter_by(classe=user_c).all()
    elif role == 'professeur':
        # Prof can see evals they created
        evals_query = Evaluation.query.filter_by(professeur=username).all()
    else:
        # Admin can see all
        evals_query = Evaluation.query.all()

    # Get "Assigned Classes" (classes where the prof has cours)
    mes_classes = []
    if role == 'professeur':
        mes_cours = Cours.query.filter_by(professeur=username).all()
        mes_classes = list(set([c.classe for c in mes_cours if c.classe]))

    return render_template('evaluations.html', 
                           role=role, 
                           evaluations=evals_query, 
                           classes_disponibles=sorted(set(classes_disponibles + mes_classes)),
                           mes_classes=mes_classes)

@app.route('/edt')
@login_required
def edt():
    # RBAC: L'accès dépend du rôle (géré ds la requête DB ou template)
    return render_template('edt.html', role=session.get('user_role', 'etudiant'))

from flask import jsonify

@app.route('/api/cours', methods=['GET', 'POST'])
@login_required
def api_cours():
    if request.method == 'GET':
        if session.get('user_role') == 'etudiant':
            user = User.query.get(session.get('user_id'))
            classe = user.classe if user and user.classe else '1'
        else:
            classe = request.args.get('classe', '1')
            
        cours_query = Cours.query.filter_by(classe=classe).all()
        
        events = [{
            'id': str(c.id),
            'title': c.title,
            'start': c.start,
            'end': c.end,
            'extendedProps': {
                'professeur': c.professeur,
                'classe': c.classe
            }
        } for c in cours_query]
        return jsonify(events)
    
    elif request.method == 'POST':
        if session.get('user_role') not in ['admin', 'professeur']:
            return jsonify({'error': 'Non autorisé'}), 403
        data = request.json
        
        prof_name = data.get('professeur')
        if session.get('user_role') == 'professeur':
            prof_name = session.get('username')
            
        nouveau_cours = Cours(
            title=data.get('title'),
            professeur=prof_name,
            start=data.get('start'),
            end=data.get('end'),
            classe=data.get('classe')
        )
        db.session.add(nouveau_cours)
        db.session.commit()
        return jsonify({'success': True, 'id': nouveau_cours.id})

@app.route('/api/cours/<int:cours_id>', methods=['PUT', 'DELETE'])
@login_required
def api_cours_detail(cours_id):
    if session.get('user_role') not in ['admin', 'professeur']:
        return jsonify({'error': 'Non autorisé'}), 403

    cours = Cours.query.get_or_404(cours_id)
    
    # Vérifier que le prof ne modifie/supprime que ses propres cours
    if session.get('user_role') == 'professeur' and cours.professeur != session.get('username'):
        return jsonify({'error': 'Ce cours appartient à un autre professeur'}), 403

    if request.method == 'PUT':
        data = request.json
        cours.title = data.get('title', cours.title)
        
        if session.get('user_role') == 'admin':
            cours.professeur = data.get('professeur', cours.professeur)
            
        cours.start = data.get('start', cours.start)
        cours.end = data.get('end', cours.end)
        db.session.commit()
        return jsonify({'success': True})
        
    elif request.method == 'DELETE':
        db.session.delete(cours)
        db.session.commit()
        return jsonify({'success': True})

# ================= ERROR HANDLERS =================
@app.errorhandler(403)
def forbidden(e):
    # Log attempt here
    print(f"Tentative d'accès non autorisé par l'utilisateur {session.get('username')} - IP: {request.remote_addr}")
    return "<h1>403 Forbidden</h1><p>Vous n'avez pas l'autorisation d'accéder à cette ressource.</p>", 403

if __name__ == '__main__':
    with app.app_context():
        # Créera les tables au lancement pour la première fois
        db.create_all() 
        
        # Création d'un utilisateur admin par défaut si la table est vide
        if not User.query.first():
            db.session.add(User(login="admin", password=generate_password_hash("admin123", method="scrypt"), role="admin", prenom="Super", nom="Admin", classe="0"))
            db.session.add(User(login="prof", password=generate_password_hash("prof123", method="scrypt"), role="professeur", prenom="Jean", nom="Prof", classe="0"))
            db.session.add(User(login="eleve", password=generate_password_hash("eleve123", method="scrypt"), role="etudiant", prenom="Alice", nom="Eleve", classe="1"))
