# Camp Life Landing — Guía de Implementación

Esta guía te lleva de **el paquete que ya tenés** → **landing publicada en internet**. Está escrita para que la pueda seguir cualquiera, tengas experiencia técnica o no. Si IT (Hamilton) lo hace, mejor todavía — pasale este documento.

**Resultado final:** una página en `camplife.marjcc.org` (o el dominio que elijan), que se actualiza sola cada vez que hacen un cambio.

---

## 📋 Resumen del flujo

```
[1] Preparar datos y cuentas
        ↓
[2] Instalar Claude Code
        ↓
[3] Claude Code arma la página (lo difícil lo hace él)
        ↓
[4] Completar los datos que faltan ([FILL IN])
        ↓
[5] Subir a GitHub
        ↓
[6] Conectar a Render.com → ¡publicada!
        ↓
[7] Apuntar el dominio
```

Tiempo estimado total: **medio día**, repartido entre vos (juntar datos) y quien buildee (2-3 horas).

---

## FASE 1 — Preparar (lo hacés vos, sin computadora técnica)

### 1.1 Juntá los datos que faltan

La página tiene "huecos" marcados como `[FILL IN]` que hay que completar. **No necesitás todos para empezar a construir**, pero sí antes de publicar. Andá juntando:

**Links externos (URLs):**
- [ ] Camp Policies — link a la página o PDF de políticas
- [ ] Staff Directory — link al directorio de staff
- [ ] Buy More T-Shirts — link al formulario de compra
- [ ] Birthday Celebration — link al formulario de cumpleaños
- [ ] Lunch Menu — link al menú semanal
- [ ] Campanion en App Store (buscá "Campanion" en el App Store y copiá el link)
- [ ] Campanion en Google Play (igual en Google Play)

**Contenido:**
- [ ] Los 9 **temas semanales** del verano (nombre de cada semana)
- [ ] **Fotos reales** del camp para la galería (4-6 buenas fotos)
- [ ] Confirmar: ¿el camp está cerrado el **3 de julio**?
- [ ] Qué camps usan **Hillel** y cuáles **Savage Playground** (carpool)

> 💡 Tip: armá un documento o mail con todo esto junto. Cuando estés en Claude Code, se lo pegás de una y completa todo de golpe.

### 1.2 Creá las cuentas

- [ ] **GitHub** → si el JCC no tiene, crear en [github.com](https://github.com) (gratis). Es donde "vive" el código.
- [ ] **Render.com** → crear en [render.com](https://render.com) (gratis). Podés registrarte con la cuenta de GitHub directamente. Es lo que publica la página en internet.

> Si Hamilton/IT ya maneja cuentas del JCC, pediles que usen las institucionales en vez de personales.

---

## FASE 2 — Instalar Claude Code (lo hace quien va a buildear)

Claude Code es una herramienta que corre en la computadora y construye el sitio por vos.

### 2.1 Requisitos previos
- Una Mac, Windows o Linux con terminal
- Una cuenta de Anthropic (la misma de Claude) con suscripción Pro/Max o acceso API

### 2.2 Instalar

**Opción A — Instalador nativo (recomendado, no necesita Node.js):**

En Mac o Linux, abrí la terminal y corré:
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

En Windows, abrí PowerShell (no CMD) y corré:
```powershell
irm https://claude.ai/install.ps1 | iex
```

Este método se actualiza solo y no necesita instalar nada más.

**Opción B — Vía npm (si ya tenés o preferís Node.js):**

Necesitás Node.js 18 o superior (de [nodejs.org](https://nodejs.org)). Después:
```bash
npm install -g @anthropic-ai/claude-code
```
⚠️ **No uses `sudo`** con este comando — causa problemas de permisos.

**Luego de instalar (cualquier método):** la primera vez que corras `claude`, te va a pedir loguearte con tu cuenta de Anthropic en el navegador.

> Si algo cambió, la guía oficial está en code.claude.com/docs

---

## FASE 3 — Construir la página (Claude Code hace el grueso)

### 3.1 Descomprimí el paquete
- Descomprimí `camplife_handoff.zip` en una carpeta (ej. en el Escritorio: `camplife/`)

### 3.2 Abrí Claude Code en esa carpeta
```bash
cd ruta/a/camplife
claude
```

### 3.3 Dale la instrucción
Escribí exactamente:
> **Read CLAUDE.md and build the landing page**

Claude Code va a:
1. Leer todas las instrucciones del proyecto
2. Armar el proyecto en **Astro** (el framework elegido)
3. Portar las 24 secciones de la página (el Hub de accesos, What to Bring, Carpool, Campanion, etc.)
4. Dejar la página corriendo localmente para que la veas en el navegador (te va a dar un link tipo `http://localhost:4321`)

### 3.4 Mirala
Abrí el link local en tu navegador. Deberías ver la página igual al modelo `camplife_landing_demo.html`.

---

## FASE 4 — Completar los datos ([FILL IN])

Ahora le pasás a Claude Code los datos que juntaste en la Fase 1. Por ejemplo:

> Acá están los links reales:
> - Camp Policies: https://...
> - Staff Directory: https://...
> - Buy T-Shirts: https://...
> - Birthday form: https://...
> - Lunch Menu: https://...
>
> Y los temas semanales son:
> - Semana 1: [tema]
> - Semana 2: [tema]
> ...

Claude Code reemplaza todos los placeholders. Para las fotos, le decís dónde están los archivos y las coloca en la galería.

> 💡 El archivo `CONTENT.md` dentro del paquete tiene tablas con TODOS los `[FILL IN]` listados, por si querés chequear que no quede ninguno.

---

## FASE 5 — Subir a GitHub

Cuando la página esté lista, le decís a Claude Code:
> **Initialize git and help me push this to GitHub**

Te va a guiar para:
1. Crear el repositorio en GitHub
2. Subir todo el código

(Si nunca usaste Git, Claude Code te explica cada paso.)

---

## FASE 6 — Publicar en Render.com

El paquete ya incluye un archivo `render.yaml` que tiene toda la configuración lista. Solo hay que conectar:

1. Entrá a [render.com](https://render.com) y logueate
2. **New → Blueprint** (o "Static Site")
3. Conectá tu cuenta de GitHub y elegí el repositorio `camplife`
4. Render lee el `render.yaml` automáticamente y configura todo:
   - Build: `npm install && npm run build`
   - Publish: carpeta `dist`
5. Click en **Create** / **Deploy**
6. En 1-2 minutos, Render te da un link tipo `https://camplife.onrender.com` → **¡ya está publicada!**

**De ahí en adelante:** cada vez que hagas un cambio y lo subas a GitHub, Render lo publica solo en ~1 minuto. No tenés que volver a tocar nada.

---

## FASE 7 — Dominio propio (camplife.marjcc.org)

Esto lo hace IT/Hamilton porque toca el DNS del JCC:

1. En Render: entrá al sitio → **Settings → Custom Domains → Add Custom Domain**
2. Escribí `camplife.marjcc.org` (o el subdominio que elijan)
3. Render te muestra un registro **CNAME** para agregar
4. Hamilton agrega ese CNAME en el panel de DNS del JCC (donde manejan marjcc.org)
5. En unos minutos/horas, `camplife.marjcc.org` muestra la página

---

## ✅ Checklist final antes de anunciar

- [ ] Todos los `[FILL IN]` reemplazados (revisá con `CONTENT.md`)
- [ ] Links externos funcionan (probá cada botón)
- [ ] Fotos reales en la galería "Moments"
- [ ] El botón "Download PDF Guide" descarga el handbook
- [ ] Probada en celular (abrila en tu teléfono)
- [ ] El chat de Sunny (WhatsApp) abre bien
- [ ] El botón Register lleva a la inscripción de CampMinder
- [ ] Dominio funcionando

---

## 🆘 Si algo se traba

- **Claude Code se confunde o se traba** → escribile qué pasó, es conversacional. Podés decirle "this isn't working, the X section looks broken" y lo arregla.
- **Render da error de build** → copiale el error a Claude Code, lo diagnostica.
- **No sé qué hacer en un paso** → preguntale a Claude Code directamente, o volvé a este chat conmigo.

---

## 📞 Mantenimiento a futuro

Para actualizar la página el año que viene (ej. Summer 2027):
1. Abrí la carpeta con Claude Code
2. Decile qué cambiar (fechas, temas, año)
3. Push a GitHub → Render lo publica solo

El archivo `CONTENT.md` te dice exactamente dónde está cada dato editable.

---

*Preparado para el equipo Hebraica · Camp Sol Taplin · MARJCC*
