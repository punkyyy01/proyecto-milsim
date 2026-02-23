// Lightweight interactions: drag & drop, inspector open, custom context menu
document.addEventListener('DOMContentLoaded', ()=>{
  const members = document.querySelectorAll('.member');
  const inspector = document.getElementById('inspector');
  const inspectorCard = document.getElementById('inspectorCard');
  const inspectorEmpty = inspector.querySelector('.inspector-empty');
  const nameEl = document.getElementById('soldierName');
  const contextMenu = document.getElementById('contextMenu');
  const exportBtn = document.getElementById('exportBtn');
  const toastWrap = document.createElement('div');
  toastWrap.className = 'toast-wrap';
  document.body.appendChild(toastWrap);

  function showToast(text){
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = text;
    toastWrap.appendChild(t);
    setTimeout(()=>{ t.style.opacity=1 },20);
    setTimeout(()=>{ t.style.opacity=0; t.addEventListener('transitionend', ()=>t.remove()) },2200);
  }

  // Track dragged element reference for reliable DOM moves
  let draggedElem = null;
  members.forEach(m=>{
    m.addEventListener('dragstart', e=>{
      e.dataTransfer.setData('text/plain', m.dataset.name);
      draggedElem = m;
      m.classList.add('dragging');
    });
    m.addEventListener('dragend', ()=>{ if(draggedElem) draggedElem.classList.remove('dragging'); draggedElem = null; });

    m.addEventListener('click', ()=>{
      inspectorEmpty.classList.add('hidden');
      inspectorCard.classList.remove('hidden');
      nameEl.textContent = m.dataset.name;
    });
  });

  // Allow dropping onto squad nodes in the left tree for quick reassign
  const tree = document.querySelectorAll('.unit-tree .node');
  tree.forEach(node=>{
    node.addEventListener('dragover', e=>{ e.preventDefault(); node.style.background='rgba(255,255,255,0.02)'; });
    node.addEventListener('dragleave', ()=>{ node.style.background=''; });
    node.addEventListener('drop', e=>{
      e.preventDefault(); node.style.background='';
      const name = e.dataTransfer.getData('text/plain');
      showToast(`Reasignado ${name} ➜ ${node.textContent.trim()}`);
    });

    // Context menu on right click
    node.addEventListener('contextmenu', e=>{
      e.preventDefault();
      showContextMenu(e.pageX, e.pageY, node);
    });
  });

  // Quick drop into squads in center (simulate move)
  const squadList = document.getElementById('squadList');
  // Make each squad a drop target and handle DOM move + confirmation
  const squads = document.querySelectorAll('.squad');
  squads.forEach(sq=>{
    sq.addEventListener('dragover', e=>{ e.preventDefault(); sq.classList.add('drop-target'); });
    sq.addEventListener('dragleave', ()=> sq.classList.remove('drop-target'));
    sq.addEventListener('drop', e=>{
      e.preventDefault(); sq.classList.remove('drop-target');
      if(!draggedElem) return;
      const oldParent = draggedElem.parentElement;
      const membersContainer = sq.querySelector('.members');
      membersContainer.appendChild(draggedElem);
      // small pop animation
      draggedElem.classList.add('pulse');
      setTimeout(()=> draggedElem.classList.remove('pulse'), 400);
      // update counts (if present)
      updateSquadCount(sq);
      const prevSquad = oldParent.closest('.squad');
      if(prevSquad) updateSquadCount(prevSquad);
      showToast(`${draggedElem.dataset.name} reasignado a ${sq.querySelector('.squad-header').textContent.trim()}`);
    });
  });

  function updateSquadCount(squadEl){
    const countEl = squadEl.querySelector('.squad-count');
    const members = squadEl.querySelectorAll('.members .member').length;
    if(countEl){
      // extract max from existing text '6/8'
      const parts = countEl.textContent.split('/');
      const max = parts[1] ? parts[1].replace(/[^0-9]/g,'') : '8';
      countEl.textContent = `${members}/${max}`;
    }
  }

  // Context menu logic
  function showContextMenu(x,y,node){
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
    contextMenu.classList.remove('hidden');
    // attach quick action
    contextMenu.querySelectorAll('li').forEach(li=>{
      li.onclick = ()=>{ alert(`${li.textContent} -> ${node.textContent.trim()}`); contextMenu.classList.add('hidden'); };
    });
  }

  document.addEventListener('click', ()=> contextMenu.classList.add('hidden'));
  // Export PNG handler
  if(exportBtn){
    exportBtn.addEventListener('click', ()=>{
      const target = document.getElementById('mainWork');
      showToast('Generando PNG...');
      html2canvas(target, {scale:2, backgroundColor: null}).then(canvas=>{
        const a = document.createElement('a');
        a.href = canvas.toDataURL('image/png');
        a.download = `milsim_peloton_${Date.now()}.png`;
        a.click();
        showToast('PNG descargado');
      }).catch(err=>{ console.error(err); showToast('Error exportando PNG'); });
    });
  }

  // Export Variants: multiple PNGs (panel, fullscreen, 4K, light theme)
  const exportVariantsBtn = document.getElementById('exportVariantsBtn');
  const exportProgress = document.getElementById('exportProgress');
  const exportList = document.getElementById('exportList');
  const closeExport = document.getElementById('closeExport');

  function addProgressItem(text){
    const li = document.createElement('li'); li.textContent = text; exportList.appendChild(li); return li;
  }

  async function exportVariant(targetSelector, name, options={}){
    const target = document.querySelector(targetSelector);
    if(!target) throw new Error('Selector no encontrado: '+targetSelector);
    if(options.theme){ document.body.classList.add(options.theme); }
    // small pause to let CSS settle
    await new Promise(r=>setTimeout(r,120));
    const canvas = await html2canvas(target, {scale: options.scale||2, backgroundColor: null, width: options.width, height: options.height});
    if(options.theme){ document.body.classList.remove(options.theme); }
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = `${name}_${Date.now()}.png`;
    a.click();
    return a.download;
  }

  async function exportAllVariants(){
    exportList.innerHTML='';
    exportProgress.classList.remove('hidden');
    const variants = [
      {selector:'#mainWork', name:'panel', options:{scale:2}},
      {selector:'.app-shell', name:'fullscreen', options:{scale:2, width:1920, height:1080}},
      {selector:'.app-shell', name:'4k', options:{scale:4, width:3840, height:2160}},
      {selector:'#mainWork', name:'panel_light', options:{scale:2, theme:'theme-light'}}
    ];

    const zip = new JSZip();
    for(const v of variants){
      const item = addProgressItem(`Generando ${v.name}...`);
      try{
        // generate canvas
        if(v.options && v.options.theme){ document.body.classList.add(v.options.theme); }
        await new Promise(r=>setTimeout(r,120));
        const target = document.querySelector(v.selector);
        if(!target) throw new Error('Selector no encontrado: ' + v.selector);
        const canvas = await html2canvas(target, {scale: v.options.scale||2, backgroundColor: null, width: v.options.width, height: v.options.height});
        if(v.options && v.options.theme){ document.body.classList.remove(v.options.theme); }
        const blob = await new Promise(res=>canvas.toBlob(res,'image/png'));
        const filename = `milsim_${v.name}_${Date.now()}.png`;
        zip.file(filename, blob);
        item.textContent = `Añadido: ${filename}`;
      }catch(err){
        item.textContent = `Error ${v.name}: ${err.message}`;
      }
    }

    addProgressItem('Comprimendo ZIP...');
    try{
      const zipBlob = await zip.generateAsync({type:'blob'});
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `milsim_variants_${Date.now()}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      addProgressItem('ZIP descargado');
      showToast('ZIP de variantes descargado');
    }catch(err){
      addProgressItem('Error comprimiendo ZIP');
      showToast('Error creando ZIP');
    }
    addProgressItem('Completado');
  }

  if(exportVariantsBtn){
    exportVariantsBtn.addEventListener('click', ()=> exportAllVariants());
  }
  if(closeExport){ closeExport.addEventListener('click', ()=> exportProgress.classList.add('hidden')) }
});
