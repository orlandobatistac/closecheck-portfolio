# 🔧 Configurar Variables y Secrets en GitHub para CI/CD

El workflow de frontend ha sido actualizado para usar **Variables y Secrets** en el build. Ahora necesitas configurarlas en GitHub.

---

## PASO 1: Agregar Variable `VITE_API_BASE_URL`

Esta es la URL pública de tu API (no es secreto).

### En GitHub:
1. Ve a tu repositorio → **Settings** → **Secrets and variables** → **Variables**
2. Click en **New repository variable**
3. Nombre: `VITE_API_BASE_URL`
4. Valor: `https://api.closecheck.orlandobatista.dev`
5. Click en **Add variable**

✅ **Variable creada:** `VITE_API_BASE_URL`

---

## PASO 2: Agregar Secret `VITE_API_KEY`

Esta es tu API key (sensible, debe estar encriptado).

### En GitHub:
1. Ve a tu repositorio → **Settings** → **Secrets and variables** → **Secrets**
2. Click en **New repository secret**
3. Nombre: `VITE_API_KEY`
4. Valor: `bdccd67db204f7ecf87e824551a357fd25cf9da593a71e639a9f07e03332725e` (tu API key del VPS)
5. Click en **Add secret**

✅ **Secret creado:** `VITE_API_KEY`

---

## PASO 3: Verificar Configuración

### En GitHub:
1. Ve a **Settings** → **Secrets and variables**

Deberías ver:

**Variables:**
```
✓ VITE_API_BASE_URL = https://api.closecheck.orlandobatista.dev
```

**Secrets:**
```
✓ VITE_API_KEY = (encriptado, no se muestra)
```

---

## PASO 4: Probar el Workflow

Ahora el frontend se desplegará automáticamente con las variables correctas:

```bash
# En tu local, haz un cambio en el frontend
cd frontend
echo "<!-- Test -->" >> src/App.jsx
git add src/App.jsx
git commit -m "test: frontend build with secrets"
git push origin main
```

### En GitHub:
1. Ve a tu repo → **Actions**
2. Verifica que el workflow de frontend **corra exitosamente**
3. El build debería incluir: `VITE_API_BASE_URL` y `VITE_API_KEY`

---

## Flujo Automático Ahora

| Evento | Backend | Frontend |
|--------|---------|----------|
| `git push` a `main` | ✅ Deploy automático | ✅ Build + Deploy automático |
| Variables | De `.env.prod` en VPS | De GitHub Variables |
| Secrets | De `.env.prod` en VPS | De GitHub Secrets |
| Resultado | API en `api.closecheck.orlandobatista.dev` | Static site en `closecheck.orlandobatista.dev` |

---

## Detalles de la Configuración

### Backend CI/CD
```
.github/workflows/deploy.yml
├── SSH al VPS
├── Git pull
├── pip install
├── Crear tablas DB
├── Restart servicio
└── Verify status
```

### Frontend CI/CD
```
.github/workflows/deploy-frontend.yml
├── Checkout code
├── Setup Node
├── npm ci
├── npm run build (con VITE_API_BASE_URL y VITE_API_KEY)
└── Deploy a GitHub Pages
```

---

## Troubleshooting

### Si el frontend build falla:
1. Verifica que las variables están correctamente creadas en GitHub
2. Revisa los logs en GitHub → Actions → Deploy Frontend
3. Busca errores de `VITE_API_BASE_URL` o `VITE_API_KEY` undefined

### Si el frontend build tiene éxito pero la API no responde:
1. Verifica que `VITE_API_BASE_URL` apunta a `https://api.closecheck.orlandobatista.dev`
2. Verifica que `VITE_API_KEY` es la key correcta del VPS
3. Abre DevTools (F12) → Console → verifica que los requests llevan `X-API-Key`

### Para regenerar API_KEY en el VPS:
```bash
ssh vps
cd /var/www/closecheck-api/backend
# Ver key actual
grep '^API_KEY=' .env

# O generar uno nuevo
openssl rand -hex 32
# Luego actualiza el .env y el GitHub Secret
```

---

## Checklist Final

```
✅ Backend Implementation
  [✓] Código implementado (auth + rate limits)
  [✓] Tests pasan (34/34)
  [✓] Variables en .env del VPS
  [✓] GitHub Actions workflow funcionando
  [✓] Servicio corriendo en producción

✅ Frontend Implementation
  [✓] Código soporta X-API-Key
  [✓] Rate limit toast UI
  [✓] GitHub Actions actualizado

⬜ GitHub Secrets & Variables (HAZLO AHORA)
  [ ] Variable: VITE_API_BASE_URL
  [ ] Secret: VITE_API_KEY
  
✅ Todo Listo
  [ ] Commit cambios en local
  [ ] Push a main
  [ ] GitHub Actions corre automáticamente
  [ ] Frontend + Backend sincronizados
```

---

## Siguientes Pasos

Una vez agregues las variables/secrets:

1. **Push cualquier cambio** (o fuerza un re-run):
   ```bash
   git commit --allow-empty -m "trigger: frontend build with secrets"
   git push origin main
   ```

2. **GitHub Actions se dispara automáticamente:**
   - Backend deployment
   - Frontend build + deployment

3. **Verifica que todo funciona:**
   ```bash
   # Test API con key
   curl -H "X-API-Key: bdccd67db204..." https://api.closecheck.orlandobatista.dev/health
   
   # Accede al frontend
   https://closecheck.orlandobatista.dev
   ```

---

¿Ya agregaste las variables y secrets en GitHub, o necesitas ayuda con algo?
