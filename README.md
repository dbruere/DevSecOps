# DevSecOps Project

## 📌 Description
Application web avec plusieurs rôles utilisateurs : élève, professeur et administrateur.

---

## mise en page : 

###  LOGIN
- [x] Connexion
- [x] Accès à l'accueil
- [x] chiffrement des passwords
- [x] JWT Token

### ACCUEIL
- [x] Nav bar
- [x] Actualité
- [x] emploi du temps de la jounée
- [x] notes récentes

### NOTES
#### Professeur
- [x] mise en place des notes
  - [x] ajouts de notes
  - [x] modification / suppression de notes
- [x] gestion accès par role
       
### EMPLOI DU TEMPS
#### étudiants
- [x] Consultation de l'emploi du temps

#### Professeur
- [x] Ajout de cours
- [x] Modification de cours
- [x] Suppression de cours

### AUTRES
- [x] mise en place du Docker
- [x] Github actions
  - [x] FLAKE8
  - [x] ZAP-SCAN
  - [x] SONAR
  - [x] PIP-AUDIT
  - [x] DOCKER
  
---
## Installation

1. Cloner le dépôt :

```bash
git clone https://github.com/dbruere/DevSecOps.git
cd DevSecOps
```

2. Générer un mot de passe sécurisé pour MySQL :

```bash
openssl rand -base64 24
```

3. Modifier les variables d’environnement MySQL dans le fichier `docker-compose.yml` avec le mot de passe généré.

4. Lancer les conteneurs Docker :

```bash
docker compose up -d
```


