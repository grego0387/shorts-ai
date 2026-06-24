# ⚡ Shorts AI — Guía de despliegue

## Estructura del proyecto
```
shorts-ai/
├── backend/          → API Python (Railway)
│   ├── main.py
│   ├── processor.py
│   ├── store.py
│   ├── requirements.txt
│   ├── railway.toml
│   └── nixpacks.toml
└── frontend/         → Interfaz React (Vercel)
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── vercel.json
    └── src/
        ├── main.jsx
        └── App.jsx
```

---

## Paso 1 — Subir el código a GitHub

1. Ve a github.com → "New repository"
2. Nombre: `shorts-ai` → Create repository
3. En tu computadora, instala Git si no lo tienes: https://git-scm.com
4. Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/shorts-ai.git
git push -u origin main
```

---

## Paso 2 — Desplegar backend en Railway

1. Ve a railway.app → New Project → Deploy from GitHub repo
2. Selecciona `shorts-ai` → carpeta `backend`
3. En "Variables" agrega:
   - `ANTHROPIC_API_KEY` = tu clave de api.anthropic.com

Railway detecta nixpacks.toml automáticamente e instala ffmpeg + Python.

4. Copia la URL pública que Railway te da (ej: `https://shorts-ai-production.up.railway.app`)

---

## Paso 3 — Desplegar frontend en Vercel

1. Ve a vercel.com → New Project → Import desde GitHub
2. Selecciona `shorts-ai` → carpeta `frontend`
3. En "Environment Variables" agrega:
   - `VITE_API_URL` = la URL de Railway del paso anterior
4. Deploy → en 2 minutos tienes tu URL pública

---

## Paso 4 — Obtener tu API Key de Anthropic

1. Ve a console.anthropic.com
2. API Keys → Create Key
3. Copia la clave y pégala en Railway como `ANTHROPIC_API_KEY`

---

## Costo estimado
| Servicio | Plan | Costo |
|---|---|---|
| GitHub | Free | $0 |
| Vercel | Hobby | $0 |
| Railway | Starter ($5 crédito) | ~$0-5/mes |
| Cloudflare R2 | Free tier | $0 |
| Anthropic API | Pay per use | ~$0.01-0.05/video |

**Total: $0 – $5/mes** dependiendo del uso.
