# multiCAD-MCP — Manual de uso

Controla tu CAD hablando con Claude. Ni macros, ni LISP, ni sintaxis rara: le
pides las cosas en castellano y él las ejecuta sobre el dibujo que tienes
abierto.

Funciona con **AutoCAD 2018+, ZWCAD 2020+, GstarCAD 2020+ y BricsCAD 21+**.
Los verticales de Autodesk (Civil 3D, Architecture, Plant 3D…) se exponen como
AutoCAD por COM, así que también valen.

---

## Empezar (3 pasos)

1. **Abre tu CAD** con el dibujo que quieras tocar. multiCAD no adivina: trabaja
   sobre el documento activo.
2. **Abre una sesión nueva de Claude** (Claude Desktop o Claude Code). Las
   conversaciones que ya tuvieras abiertas antes de instalar no lo verán.
3. **Pídele algo.** La conexión se establece sola en la primera orden.

> Prueba de humo: *"¿Estás conectado al CAD? Dime qué dibujo tengo abierto."*

---

## Cómo se le habla

En lenguaje natural. Claude traduce tu petición a las herramientas del
servidor; tú no escribes comandos.

Sí funciona:

- *"Dibuja un círculo rojo en 50,50 con radio 25"*
- *"Crea la capa INSTALACIONES en azul y mueve ahí todas las líneas de la capa 0"*
- *"Apaga todas las capas menos ARQUITECTURA"*
- *"Sácame a Excel todas las entidades del dibujo con su capa y su longitud"*

Dos costumbres que ayudan mucho:

- **Coordenadas explícitas** cuando importen: `"0,0"`, `"120.5,-30"`, `"10,10,5"`.
  No sabe dónde estás mirando ni qué has clicado.
- **Trabaja por capas.** Si le dices en qué capa dejar cada cosa, luego puedes
  seleccionar, colorear o borrar por capa de un tirón.

---

## Qué sabe hacer

Siete herramientas que suman más de 50 comandos de CAD.

### 1. Sesión y conexión

Conectar, desconectar, ver el estado, detectar si hay un CAD corriendo sin
lanzarlo, y listar los CAD soportados.

*"¿A qué CAD estás conectado y qué dibujos tengo abiertos?"*

### 2. Dibujo

| Entidad | Qué le pides |
|---|---|
| Línea | *"Línea de 0,0 a 100,0 en rojo, capa MUROS"* |
| Círculo | *"Círculo en 50,40 de radio 10, azul"* |
| Arco | *"Arco en 0,0 radio 5 de 0 a 90 grados"* |
| Rectángulo | *"Rectángulo de 0,0 a 20,15"* |
| Polilínea | *"Polilínea cerrada por 0,0 · 10,10 · 20,0"* |
| Spline | *"Spline que pase por 0,0 · 5,10 · 10,0"* |
| Texto | *"Pon el texto 'PLANTA BAJA' en 5,5 con altura 2.5"* |
| Cota | *"Acota de 0,0 a 10,0"* |
| Directriz | *"Directriz desde 0,0 hasta 10,10 con el texto 'revisar'"* |
| Directriz múltiple | *"Una directriz con dos flechas apuntando a 0,0 y 20,0 con la etiqueta 'PILAR'"* |
| **Tabla** | *"Inserta en 0,0 una tabla 'Precios' con columnas Item, Cantidad, Valor y estas filas: Acero 10 150, Mano de obra 5 120"* |

Por defecto: color `white`, capa `0`.
Colores por nombre: red, blue, green, yellow, cyan, magenta, white, black,
gray, orange.

### 3. Capas

Crear (con color y grosor), borrar, renombrar, encender y apagar (varias de
golpe), cambiar color, consultar si está visible, listar, y ver el detalle
completo (color, bloqueada, congelada).

*"Crea CIMENTACIÓN en rojo con grosor 50"*
*"Apaga Defpoints y NOTAS"*
*"Lístame todas las capas con su color y cuáles están bloqueadas"*

### 4. Bloques

Listar la biblioteca, ver información y referencias de un bloque, insertar
(con escala, rotación, capa y color), y **crear bloques** a partir de entidades
existentes o de lo que tengas seleccionado.

Y lo más útil en trabajo real, los **atributos**:

- *"Léeme los atributos de este bloque"* → devuelve TAG y valor
- *"Cámbiale el atributo POLOS a 4P"* → escritura directa

*"Inserta el bloque PUERTA en 10,20 a escala 1.5 girado 90 grados en la capa CARPINTERÍA"*

### 5. Entidades

**Seleccionar** por capa, por tipo o por color. Y sobre lo seleccionado:
mover, girar, escalar (con centro), cambiar color, cambiar de capa, poner el
color ByLayer, copiar, pegar y borrar.

Tipos reconocidos: LINE, CIRCLE, ARC, LWPOLYLINE, POLYLINE, TEXT, MTEXT,
INSERT, DIMENSION, SPLINE, POINT, HATCH.

*"Selecciona todos los círculos y ponlos en la capa TALADROS con color ByLayer"*
*"Coge todo lo que haya en la capa TEMP y bórralo"*

### 6. Archivos y sesión múltiple

Guardar en **DWG, DXF o PDF**, crear dibujo nuevo, cerrar (guardando o no),
listar los dibujos abiertos y **cambiar de uno a otro**.

*"Guarda esto como REVISION_C.dwg"*
*"Expórtame el dibujo a PDF"*
*"Cámbiate al dibujo planta_primera.dwg y dime cuántas entidades tiene"*

### 7. Extracción de datos y Excel

Saca el contenido del dibujo como JSON o como Excel de 3 hojas (Entidades,
Capas, Bloques), **de todo el dibujo o solo de lo que tengas seleccionado en
pantalla**.

Columnas del Excel: Handle, ObjectType, Layer, Color, Length, Area, Radius,
Circumference, Name.

*"Selecciono yo en pantalla y me exportas solo eso a Excel"*
*"Dame en JSON todas las polilíneas de la capa PARCELAS con su área"*

Los ficheros salen por defecto a `Documentos\multiCAD Exports`.

### 8. Vista y capturas

Zoom a extensión, deshacer y rehacer (varios pasos), captura de la ventana, y
`export_view`, que renderiza el dibujo internamente — funciona aunque la
ventana del CAD esté tapada por otra.

*"Haz zoom a todo y mándame una captura"*
*"Deshaz las últimas 3 acciones"*

---

## Tareas completas, no solo comandos sueltos

Lo interesante es encadenar. Ejemplos reales que resuelve de una sola petición:

- *"Dibuja la gráfica de y = sen(x) entre 0 y 360 grados, con los ejes rotulados y una cuadrícula cada 30 grados"*
- *"Monta un cuadro de rótulo en la esquina inferior derecha con estos datos: proyecto, cliente, escala y fecha"*
- *"Recorre todos los bloques de cuadro eléctrico, léeles el atributo POTENCIA y hazme una tabla resumen dentro del dibujo"*
- *"Audita el dibujo: dime qué capas están vacías, qué bloques no se usan y qué entidades tienen color forzado en vez de ByLayer"*

---

## El dashboard web

Vista en tiempo real del estado del CAD, en `http://localhost:8888`.

Ábrelo desde el panel de multiCAD-MCP (acceso directo del menú Inicio), o
pidiéndoselo a Claude: *"Ábreme el dashboard"*.

Muestra la conexión y el dibujo activo, el recuento de entidades, la lista de
capas (con interruptor de visibilidad), la biblioteca de bloques y un
explorador de entidades filtrable por tipo. Tiene botón **Refresh Now** para
sincronizar a mano.

---

## Ajustes

El fichero editable está en `%LOCALAPPDATA%\multiCAD-mcp\config.json`:

| Ajuste | Para qué |
|---|---|
| `dashboard.port` | Cambia el puerto si el 8888 te lo ocupa otro programa |
| `logging_level` | `DEBUG` para diagnosticar, `INFO` normal |
| `output.directory` | Dónde caen exportaciones y guardados |
| `cad.<nombre>.startup_wait_time` | Súbelo si tu CAD tarda en arrancar |
| `output.allow_arbitrary_paths` | Permite guardar en cualquier ruta absoluta |

Tras tocarlo, **reinicia la sesión de Claude**.

---

## Si algo no va

**"No veo multiCAD en Claude"** — Los servidores MCP se cargan al arrancar la
sesión. Cierra Claude del todo y ábrelo de nuevo. En Claude Code compruébalo
con `claude mcp list` (debe salir `multicad ... Connected`).

**"Connection failed" o "Not connected"** — El CAD tiene que estar abierto.
Pídele *"comprueba el estado de la conexión"*; si sigue, reinicia el CAD.
Ojo con abrir el CAD **como administrador**: si Claude no lo es, COM no los
deja hablar.

**Dibuja pero no lo veo** — Casi siempre es la vista: *"haz zoom a todo"*.
O la capa está apagada.

**Va lento en dibujos enormes** — En dibujos de más de 10.000 entidades,
selecciona por capa o por tipo en vez de pedir "todo".

**Los logs** están en `%LOCALAPPDATA%\multiCAD-mcp\logs\multicad_mcp.log`.

---

## Qué no hace (todavía)

- No **ve** el dibujo: trabaja con datos y coordenadas, no interpreta lo que
  hay dibujado a partir de una imagen. Puede hacerte una captura, pero no
  selecciona "lo que se parece a una puerta".
- No hay **modelado 3D** de sólidos ni superficies.
- No accede a la selección del usuario salvo donde está previsto
  (`export_data` con alcance "seleccionado" y creación de bloques).
- Nada de esto sale de tu ordenador: la conexión con el CAD es local por COM.

---

## Recordatorio de seguridad

Puede **borrar, mover y sobrescribir** de verdad. Antes de soltarle una tanda
grande sobre un plano bueno: guarda. Si algo sale torcido, *"deshaz las últimas
N acciones"* suele bastar, pero el `Ctrl+S` previo no falla nunca.
