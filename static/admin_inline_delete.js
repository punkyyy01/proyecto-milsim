/**
 * admin_inline_delete.js
 * Unifica TODOS los botones de eliminar en inlines de Django/Jazzmin:
 * 1. Checkboxes DELETE (filas existentes) -> Botón rojo con confirmación
 * 2. Links inline-deletelink (filas dinámicas) -> Mismo estilo
 */
(function() {
    'use strict';

    function initInlineDelete() {
        // =============================================
        // PARTE 1: Checkboxes DELETE (registros guardados)
        // =============================================
        const deleteCheckboxes = document.querySelectorAll(
            'input[type="checkbox"][id$="-DELETE"]'
        );

        deleteCheckboxes.forEach(function(checkbox) {
            const row = checkbox.closest('tr') || checkbox.closest('.inline-related');
            if (!row) return;

            const cell = checkbox.closest('td') || checkbox.closest('.field-DELETE') || checkbox.parentElement;

            // Ocultar checkbox original y su label
            checkbox.style.display = 'none';
            const label = cell.querySelector('label');
            if (label) label.style.display = 'none';

            // No duplicar
            if (cell.querySelector('.btn-inline-delete')) return;

            // Crear botón ELIMINAR
            const btnDelete = document.createElement('button');
            btnDelete.type = 'button';
            btnDelete.className = 'btn-inline-delete';
            btnDelete.innerHTML = '<i class="fas fa-trash-alt"></i> ELIMINAR';

            // Crear botón DESHACER
            const btnUndo = document.createElement('button');
            btnUndo.type = 'button';
            btnUndo.className = 'btn-inline-undo';
            btnUndo.innerHTML = '<i class="fas fa-undo"></i> DESHACER';
            btnUndo.style.display = 'none';

            btnDelete.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!confirm('¿Eliminar este elemento? Se aplicará al guardar.')) return;

                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                row.classList.add('inline-marked-delete');
                btnDelete.style.display = 'none';
                btnUndo.style.display = 'inline-flex';
            });

            btnUndo.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                checkbox.checked = false;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                row.classList.remove('inline-marked-delete');
                btnUndo.style.display = 'none';
                btnDelete.style.display = 'inline-flex';
            });

            cell.appendChild(btnDelete);
            cell.appendChild(btnUndo);
        });

        // =============================================
        // PARTE 2: Links inline-deletelink (filas dinámicas nuevas)
        // =============================================
        const deleteLinks = document.querySelectorAll('.inline-deletelink');

        deleteLinks.forEach(function(link) {
            // No duplicar si ya procesamos este link
            if (link.classList.contains('btn-inline-delete')) return;
            if (link.parentElement && link.parentElement.querySelector('.btn-inline-delete')) return;

            // Guardar la función original de click
            const originalHref = link.getAttribute('href');

            // Reemplazar con nuestro estilo
            link.className = 'btn-inline-delete';
            link.innerHTML = '<i class="fas fa-trash-alt"></i> ELIMINAR';
            link.style.cssText = ''; // Limpiar estilos inline

            // Envolver el click con confirmación
            link.addEventListener('click', function(e) {
                if (!confirm('¿Quitar esta fila?')) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }
            }, true);
        });

        // =============================================
        // PARTE 3: Cabecera "¿Eliminar?" → "ACCIONES"
        // =============================================
        document.querySelectorAll('.tabular thead th').forEach(function(th) {
            const text = th.textContent.trim().toLowerCase();
            if (text.includes('eliminar') || text.includes('delete')) {
                th.innerHTML = '<span class="inline-delete-header">ACCIONES</span>';
            }
        });
    }

    // Ejecutar al cargar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInlineDelete);
    } else {
        initInlineDelete();
    }

    // Re-ejecutar con nuevos inlines dinámicos
    document.addEventListener('formset:added', function() {
        setTimeout(initInlineDelete, 150);
    });

    // MutationObserver para cualquier cambio dinámico
    const observer = new MutationObserver(function(mutations) {
        let shouldReinit = false;
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && (
                    (node.classList && (
                        node.classList.contains('inline-related') ||
                        node.classList.contains('form-row')
                    )) ||
                    (node.querySelector && (
                        node.querySelector('input[id$="-DELETE"]') ||
                        node.querySelector('.inline-deletelink')
                    ))
                )) {
                    shouldReinit = true;
                }
            });
        });
        if (shouldReinit) {
            setTimeout(initInlineDelete, 150);
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
})();
