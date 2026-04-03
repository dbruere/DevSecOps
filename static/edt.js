document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    let currentSelectionInfo = null;
    let currentEditInfo = null;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',

        locale: 'fr',
        firstDay: 1, // 1 = Lundi, 0 = Dimanche (par d�faut)
        buttonText: {
            today: "Aujourd'hui",
            month: 'Mois',
            week: 'Semaine',
            day: 'Jour'
        },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '08:00:00',
        slotMaxTime: '19:00:00',
        allDaySlot: false, 
        events: function(info, successCallback, failureCallback) {
            let selectedClass = document.getElementById('classSelector').value;
            fetch('/api/cours?classe=' + encodeURIComponent(selectedClass))
                .then(response => response.json())
                .then(data => successCallback(data))
                .catch(error => failureCallback(error));
        },
        selectable: window.userRole === 'admin' || window.userRole === 'professeur',
        editable: false, 
        // Personnalisation de l'affichage du cours pour inclure le professeur
        eventContent: function(arg) {
            let timeText = arg.timeText;
            let title = arg.event.title;
            let prof = arg.event.extendedProps.professeur || '';
            
            return {
                html: `<div class="fc-event-main-frame" style="padding:2px;">
                        <div class="fc-event-time" style="font-weight:bold;">${timeText}</div>
                        <div class="fc-event-title-container">
                            <div class="fc-event-title fc-sticky">${title}</div>
                            <div class="fc-event-title fc-sticky" style="font-size:0.85em; opacity:0.9;">${prof}</div>
                        </div>
                       </div>`
            };
        },

        // 2. CREER UN COURS
        select: function(info) {
            if (window.userRole !== 'admin' && window.userRole !== 'professeur') return;
            currentSelectionInfo = info;

            // On vide et on pr�-remplit les champs de la modale
            document.getElementById('eventTitle').value = '';
            
            let profInput = document.getElementById('eventProfesseur');
            if (window.userRole === 'professeur') {
                profInput.value = window.userName;
                profInput.readOnly = true;
            } else {
                profInput.value = '';
                profInput.readOnly = false;
            }

            // Formatage de la date gliss�e pour l'afficher sous forme d'heures (HH:MM)
            let startD = new Date(info.startStr);
            let endD = new Date(info.endStr);
            
            document.getElementById('eventStart').value = startD.toTimeString().slice(0,5);
            document.getElementById('eventEnd').value = endD.toTimeString().slice(0,5);

            document.getElementById('addEventModal').showModal();
        },

        // 3. EDITER OU SUPPRIMER UN COURS
        eventClick: function(info) {
            if (window.userRole !== 'admin' && window.userRole !== 'professeur') return;
            
            let profAssigned = info.event.extendedProps.professeur || '';
            if (window.userRole === 'professeur' && profAssigned !== window.userName) {
                alert("Vous ne pouvez pas modifier un cours qui ne vous appartient pas.");
                return;
            }

            currentEditInfo = info;

            document.getElementById('editEventTitle').value = info.event.title;
            
            let editProfInput = document.getElementById('editEventProfesseur');
            editProfInput.value = profAssigned;
            if (window.userRole === 'professeur') {
                editProfInput.readOnly = true;
            } else {
                editProfInput.readOnly = false;
            }

            // R�cup�rer les dates de l'�v�nement et les formater pour les inputs "time"
            let startD = new Date(info.event.start);
            let endD = info.event.end ? new Date(info.event.end) : new Date(startD.getTime() + 60*60*1000);
            
            let sHours = startD.getHours().toString().padStart(2, '0');
            let sMinutes = startD.getMinutes().toString().padStart(2, '0');
            let eHours = endD.getHours().toString().padStart(2, '0');
            let eMinutes = endD.getMinutes().toString().padStart(2, '0');

            document.getElementById('editEventStart').value = `${sHours}:${sMinutes}`;
            document.getElementById('editEventEnd').value = `${eHours}:${eMinutes}`;

            document.getElementById('editEventModal').showModal();
        },
        
        // 4. DEPLACER OU REDIMENSIONNER UN COURS
        eventChange: function(info) {
            fetch('/api/cours/' + info.event.id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: info.event.title,
                    start: info.event.startStr,
                    end: info.event.endStr
                })
            });
        }
    });

    calendar.render();

      let selectContainer = document.getElementById('selecteur_container');
      if (selectContainer) {
          let rightToolbar = document.querySelector('.fc-toolbar-chunk:nth-child(3)');
          if (rightToolbar) {
              selectContainer.style.display = 'inline-block';
              selectContainer.style.verticalAlign = 'middle';
              rightToolbar.style.display = 'flex';
              rightToolbar.style.alignItems = 'center';
              rightToolbar.appendChild(selectContainer);
          }
          let selectTarget = document.getElementById('classSelector');
          if (selectTarget && selectTarget.tagName.toLowerCase() === 'select') {
              selectTarget.addEventListener('change', function() { calendar.refetchEvents(); });
          }
      }

    

    // --- AJOUTER LE COURS MANUELLEMENT ---
    document.getElementById('saveEventBtn').addEventListener('click', function() {
        let title = document.getElementById('eventTitle').value;
        let professeur = document.getElementById('eventProfesseur').value;
        let setStart = document.getElementById('eventStart').value;
        let setEnd = document.getElementById('eventEnd').value;
        
        if (title && title.trim() !== "" && currentSelectionInfo && setStart && setEnd) {
            
            // Reconstruire la vraie date � partir de l'heure modifi�e dans le pop-up
            let originalStart = new Date(currentSelectionInfo.startStr);
            let newStartStr = originalStart.toISOString().split('T')[0] + 'T' + setStart + ':00';
            
            let originalEnd = new Date(currentSelectionInfo.endStr);
            // Corriger le bug du passage � minuit si l'heure de fin est inf�rieure � l'heure de d�but
            let finalEndStr = originalEnd.toISOString().split('T')[0] + 'T' + setEnd + ':00';
            
            let selectedClass = document.getElementById('classSelector').value;

            fetch('/api/cours', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    professeur: professeur,
                    start: newStartStr,
                    end: finalEndStr,
                    classe: selectedClass
                })
            })
            .then(res => res.json())
            .then(data => {
                calendar.refetchEvents(); // On rafra�chit le calendrier avec le serveur
                document.getElementById('addEventModal').close();
                calendar.unselect();
                currentSelectionInfo = null;
            });
        }
    });

    // --- ENREGISTRER LES MODIFICATIONS D'UN COURS ---
    document.getElementById('updateEventBtn').addEventListener('click', function() {
        if (currentEditInfo) {
            let newTitle = document.getElementById('editEventTitle').value;
            let newProf = document.getElementById('editEventProfesseur').value;
            let setStart = document.getElementById('editEventStart').value;
            let setEnd = document.getElementById('editEventEnd').value;
            
            if (newTitle && newTitle.trim() !== "" && setStart && setEnd) {
                // Reconstruire de fa�on simple (en gardant la date d'origine et en rempla�ant juste l'heure locale)
                let datePartStart = currentEditInfo.event.startStr.split('T')[0];
                let datePartEnd = currentEditInfo.event.endStr ? currentEditInfo.event.endStr.split('T')[0] : datePartStart;
                
                let updatedStartStr = datePartStart + 'T' + setStart + ':00';
                let updatedEndStr = datePartEnd + 'T' + setEnd + ':00';

                fetch('/api/cours/' + currentEditInfo.event.id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: newTitle,
                        professeur: newProf,
                        start: updatedStartStr,
                        end: updatedEndStr
                    })
                }).then(() => {
                    currentEditInfo.event.setProp('title', newTitle);
                    currentEditInfo.event.setExtendedProp('professeur', newProf);
                    currentEditInfo.event.setDates(updatedStartStr, updatedEndStr);
                    document.getElementById('editEventModal').close();
                    currentEditInfo = null;
                });
            }
        }
    });

    // --- SUPPRIMER UN COURS DEPUIS LA MODALE DE GESTION ---
    document.getElementById('deleteEventBtn').addEventListener('click', function() {
        if (currentEditInfo) {
            fetch('/api/cours/' + currentEditInfo.event.id, {
                method: 'DELETE'
            }).then(() => {
                currentEditInfo.event.remove(); 
                document.getElementById('editEventModal').close();
                currentEditInfo = null;
            });
        }
    });

});
