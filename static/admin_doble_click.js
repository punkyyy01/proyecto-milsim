/* static/js/admin_doble_click.js */
window.addEventListener('load', function() {
    // Cambia 'cursos' por el nombre de tu campo si lo usas en otros lados
    const fieldName = 'cursos'; 
    
    const fromSelect = document.getElementById(`id_${fieldName}_from`);
    const toSelect = document.getElementById(`id_${fieldName}_to`);

    // Función auxiliar para mover elementos usando la API interna de Django
    function moveOption(direction) {
        const source = direction === 'add' ? fromSelect : toSelect;
        const target = direction === 'add' ? toSelect : fromSelect;
        
        // Verificamos que se haya seleccionado algo
        if (source.selectedIndex !== -1) {
            // SelectBox es la librería global de Django que maneja estos widgets
            SelectBox.move(`id_${fieldName}`, direction === 'add' ? 'from' : 'to', direction === 'add' ? 'to' : 'from');
        }
    }

    if (fromSelect && toSelect) {
        // Doble click en la lista izquierda (Disponibles) -> Mover a derecha
        fromSelect.addEventListener('dblclick', function(e) {
            moveOption('add');
        });

        // Doble click en la lista derecha (Elegidos) -> Mover a izquierda
        toSelect.addEventListener('dblclick', function(e) {
            moveOption('remove');
        });
    }
});