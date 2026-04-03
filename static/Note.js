// static/js/script.js

// On attend que la page soit entièrement chargée avant d'exécuter le script
document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Récupération des informations depuis info.txt
    async function loadInfoTxt() {
        const infoElement = document.getElementById('info');
        if (!infoElement) return;

        try {
            const res = await fetch('/static/info.txt');
            if (!res.ok) throw new Error('Erreur HTTP ' + res.status);
            const text = await res.text();
            infoElement.textContent = text;
        } catch (err) {
            infoElement.textContent = "Impossible de charger les informations statiques.";
            console.error("Erreur de chargement:", err);
        }
    }

    // Appel de la fonction
    loadInfoTxt();

    // 2. Validation côté client du formulaire (Sécurité de base)
    const noteForm = document.getElementById('form-note');
    if (noteForm) {
        noteForm.addEventListener('submit', function(event) {
            const valeurInput = document.getElementById('valeur-note');
            const note = parseFloat(valeurInput.value);

            // Vérifie si la note est valide
            if (note < 0 || note > 20) {
                event.preventDefault(); // Bloque l'envoi du formulaire
                alert("Erreur de saisie : La note doit être comprise entre 0 et 20.");
                valeurInput.style.border = "2px solid red";
            }
        });
    }
});