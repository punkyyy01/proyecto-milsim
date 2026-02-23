# MILSIM Dashboard — Mockup

Archivos generados:
- `index.html` — pantalla principal del mockup
- `styles.css` — estilos (tema oscuro, layout multipanel)
- `script.js` — interacciones ligeras (arrastrar/soltar, menú contextual, inspector)

Cómo ver el mockup:
1. Abrir [designs/milsim-dashboard/index.html](designs/milsim-dashboard/index.html) en el navegador.
2. Probar arrastrar un miembro desde una escuadra y soltarlo en otra escuadra o en una unidad del árbol izquierdo.
3. Clic en un miembro para abrir el inspector derecho.
4. Clic derecho sobre una unidad en el árbol para ver menú contextual.

Exportar PNG de alta resolución:

- Hay un botón `Exportar PNG` en la cabecera del área de trabajo.
- Al pulsarlo, el mockup usa `html2canvas` para generar una imagen PNG del panel central (`Pelotón`) a 2x de resolución y la descarga automáticamente.
- Si necesitas PNGs a otras resoluciones o composiciones, abre el archivo en un navegador y usa la herramienta de export.

- Hay un botón `Exportar PNG` en la cabecera del área de trabajo.
- Al pulsarlo, el mockup usa `html2canvas` para generar una imagen PNG del panel central (`Pelotón`) a 2x de resolución y la descarga automáticamente.
- También hay un botón `Exportar variantes` que genera automáticamente varias versiones:
	- `panel` (panel central) a 2x
	- `fullscreen` (captura de la `app-shell` a 1920×1080)
	- `4k` (captura de la `app-shell` a 3840×2160)
	- `panel_light` (misma captura del panel, con tema claro aplicado)

	El botón abre un diálogo de progreso y empaqueta todas las variantes en un único ZIP que se descarga automáticamente.

	Nota: la página usa `JSZip` cliente-side para crear el ZIP, y `html2canvas` para generar los PNGs.

Notas técnicas:
- El mockup incluye animaciones sutiles y una confirmación tipo "toast" para las reasignaciones.
- Arrastrar/soltar actualiza el DOM localmente y recalcula los contadores visibles.


Notas de diseño rápidas:
- Layout multipantalla: panel izquierdo (árbol), panel central (zona de trabajo), panel derecho (inspector).
- Arrastrar/soltar soportado tanto sobre el árbol como sobre escuadras.
- Indicadores visuales: conteo `6/8` y puntos de color para preparación.
