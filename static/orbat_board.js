(function(){
  // Drag & Drop básico y llamadas al endpoint transferir_personal
  const board = document.getElementById('board');
  let dragged = null;

  document.addEventListener('dragstart', (e)=>{
    const card = e.target.closest('.card');
    if(!card) return;
    dragged = card;
    e.dataTransfer.setData('text/plain', card.dataset.personaId);
    setTimeout(()=>card.classList.add('dragging'), 0);
  });
  document.addEventListener('dragend', (e)=>{
    if(dragged) dragged.classList.remove('dragging');
    dragged = null;
  });

  // Make columns drop targets
  document.querySelectorAll('.cards').forEach(col=>{
    col.addEventListener('dragover', (e)=>{
      e.preventDefault();
      col.classList.add('drag-over');
    });
    col.addEventListener('dragleave', ()=>col.classList.remove('drag-over'));

    col.addEventListener('drop', async (e)=>{
      e.preventDefault();
      col.classList.remove('drag-over');
      const personaId = e.dataTransfer.getData('text/plain');
      const destinoId = col.dataset.escuadraId;
      if(!personaId || !destinoId) return;

      // Call backend
      try{
        const resp = await fetch('/api/transferir_personal/',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({persona_id: Number(personaId), escuadra_destino_id: Number(destinoId)})
        });

        if(resp.status === 200){
          // Move DOM node
          const card = document.querySelector(`.card[data-persona-id="${personaId}"]`);
          if(card) col.appendChild(card);
          return;
        }

        if(resp.status === 409){
          const data = await resp.json();
          openConflictModal(destinoId, personaId, data.miembros || []);
          return;
        }

        const j = await resp.json().catch(()=>({}));
        alert('Error al mover: '+(j.error||resp.status));
      }catch(err){
        console.error(err);
        alert('Error de red o servidor');
      }
    });
  });

  // Modal handling
  const modal = document.getElementById('modal');
  const modalList = document.getElementById('modal-list');
  const modalCancel = document.getElementById('modal-cancel');
  let currentDestino = null;
  let currentPersona = null;

  modalCancel.addEventListener('click', closeModal);

  function openConflictModal(destinoId, personaId, miembros){
    currentDestino = destinoId; currentPersona = personaId;
    modalList.innerHTML = '';
    miembros.forEach(m=>{
      const li = document.createElement('li');
      li.textContent = m.nombre_milsim + ' — ' + m.rango;
      const btn = document.createElement('button');
      btn.className = 'btn btn-primary';
      btn.textContent = 'Intercambiar';
      btn.addEventListener('click', ()=>confirmSwap(m.id));
      li.appendChild(btn);
      modalList.appendChild(li);
    });
    modal.classList.remove('hidden');
  }

  function closeModal(){
    modal.classList.add('hidden');
    modalList.innerHTML = '';
    currentDestino = currentPersona = null;
  }

  async function confirmSwap(reemplazarId){
    if(!currentPersona || !currentDestino) return;
    try{
      const resp = await fetch('/api/transferir_personal/',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({persona_id: Number(currentPersona), escuadra_destino_id: Number(currentDestino), persona_a_reemplazar_id: Number(reemplazarId)})
      });

      if(resp.status === 200){
        const card = document.querySelector(`.card[data-persona-id="${currentPersona}"]`);
        const destinoCol = document.querySelector(`.cards[data-escuadra-id="${currentDestino}"]`);
        if(card && destinoCol) destinoCol.appendChild(card);

        // If backend moved the replaced person to origin, update DOM by removing replaced from destination and appending to origin if present in DOM
        const payload = await resp.json().catch(()=>({}));
        if(payload.replaced){
          // Try to find replaced card and move it to the origin column if known
          const replacedCard = document.querySelector(`.card[data-persona-id="${payload.replaced}"]`);
          if(replacedCard){
            const originId = payload.replaced_moved_to;
            if(originId){
              const originCol = document.querySelector(`.cards[data-escuadra-id="${originId}"]`);
              if(originCol) originCol.appendChild(replacedCard);
            } else {
              // If moved to None (HQ), remove from columns
              replacedCard.remove();
            }
          }
        }

        closeModal();
        return;
      }

      const j = await resp.json().catch(()=>({}));
      alert('Error al intercambiar: '+(j.error||resp.status));
    }catch(err){
      console.error(err);
      alert('Error de red o servidor');
    }
  }
})();
