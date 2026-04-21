# ✅ PASOS MANUALES REQUERIDOS PARA COMPLETAR LA IMPLEMENTACIÓN

La implementación de código está **100% completa** y **el CI/CD está automático**.  
Solo necesitas hacer estos **3 pasos manuales**:

---

## PASO 1: Restartar el Servicio en Producción

Ejecuta esto en el VPS para aplicar las nuevas variables de entorno:

```bash
ssh vps
sudo systemctl restart closecheck-api.service

# Verificar que el servicio está corriendo
sudo systemctl status closecheck-api.service

# Ver los logs (presiona Ctrl+C para salir)
sudo journalctl -u closecheck-api.service -f
```

**Espera 5-10 segundos para que el servicio inicie completamente.**

---

## PASO 2: Verificar que Todo Funciona (Test de Validación)

Desde tu máquina local (NO en el VPS), ejecuta estos tests:

### Test 1: Sin API Key → Debe dar **401**
```bash
curl -X POST https://api.closecheck.orlandobatista.dev/api/v1/validate \
  -F "files=@test.pdf" \
  -F "transaction_type=residential"
```

**Respuesta esperada:**
```json
{
  "detail": "Missing or invalid API key"
}
```

---

### Test 2: Con API Key válido → Debe dar **202**

Primero obtén tu API_KEY desde el .env del VPS:

```bash
ssh vps "grep '^API_KEY=' /var/www/closecheck-api/backend/.env | cut -d= -f2"
```

Luego haz el request:

```bash
API_KEY="<paste-key-aqui>"

curl -X POST https://api.closecheck.orlandobatista.dev/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test.pdf" \
  -F "transaction_type=residential"
```

**Respuesta esperada:**
```json
{
  "job_id": "some-uuid",
  "status": "queued"
}
```

---

### Test 3: Rate Limiting (Upload) → Segundo debe dar **429**

```bash
API_KEY="<tu-api-key>"

# Primer upload - debe pasar (202)
echo "Primer upload..."
curl -X POST https://api.closecheck.orlandobatista.dev/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test1.pdf" \
  -F "transaction_type=residential"

echo ""
echo "Esperando 1 segundo..."
sleep 1

# Segundo upload inmediato - debe bloquearse (429)
echo "Segundo upload (debería retornar 429)..."
curl -X POST https://api.closecheck.orlandobatista.dev/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test2.pdf" \
  -F "transaction_type=residential"
```

**Respuesta esperada para el 2do:**
```json
{
  "detail": "Rate limit exceeded. Please wait Xs before uploading again.",
  "retry_after_seconds": 9
}
```

---

### Test 4: Después de esperar → Debe pasar (202)

```bash
API_KEY="<tu-api-key>"

# Esperar 10 segundos
echo "Esperando 10 segundos para que se cumpla cooldown..."
sleep 10

# Tercer upload - debe pasar (202)
echo "Tercer upload (debería pasar después de cooldown)..."
curl -X POST https://api.closecheck.orlandobatista.dev/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test3.pdf" \
  -F "transaction_type=residential"
```

---

## PASO 3: Verificar Base de Datos

Conectate al VPS y verifica que las nuevas tablas fueron creadas:

```bash
ssh vps

# Entrar a la DB SQLite
cd /var/www/closecheck-api/backend
sqlite3 closecheck.db

# Dentro de sqlite3, ejecuta:
.tables

# Deberías ver algo como:
# email_draft_limits  upload_rate_limits  ...otras_tablas...

# Ver estructura de email_draft_limits
.schema email_draft_limits

# Ver estructura de upload_rate_limits  
.schema upload_rate_limits

# Salir
.quit
```

---

## ✅ Checklist de Validación

- [ ] **Paso 1:** Servicio restarted y running
- [ ] **Paso 2.1:** Sin API Key → 401 ✓
- [ ] **Paso 2.2:** Con API Key → 202 ✓
- [ ] **Paso 2.3:** Segundo upload sin esperar → 429 ✓
- [ ] **Paso 2.4:** Tercer upload después de esperar → 202 ✓
- [ ] **Paso 3:** Tablas `email_draft_limits` y `upload_rate_limits` existen en DB ✓

**Una vez completes estos 3 pasos, la implementación está 100% lista.**

---

## Qué Pasa Automáticamente de Ahora en Adelante

Cada vez que hagas `git push` a `main`:

1. ✅ **GitHub Actions** se dispara automáticamente
2. ✅ **SSH al VPS** - ejecuta el deployment
3. ✅ **Git pull** - código actualizado
4. ✅ **pip install** - dependencias instaladas
5. ✅ **Crear tablas** - si son nuevas (idempotente)
6. ✅ **Import validation** - verifica que todos los módulos cargan
7. ✅ **Service restart** - reinicia el servicio
8. ✅ **Status check** - verifica que el servicio está running

---

## Troubleshooting

### Si el servicio no inicia:
```bash
ssh vps
sudo journalctl -u closecheck-api.service -n 50
# Busca el error
```

### Si los tests fallan:
```bash
ssh vps
cd /var/www/closecheck-api/backend

# Verificar que .env tiene las nuevas variables
grep API_KEY_REQUIRED .env
grep EMAIL_DRAFT_LIMIT_PER_JOB .env
grep UPLOAD_RATE_LIMIT_SECONDS .env

# Verificar imports
venv/bin/python -c "from app.api.deps.auth import verify_api_key; print('✓ Auth OK')"
venv/bin/python -c "from app.api.deps.email_limit import check_email_draft_limit; print('✓ Email Limit OK')"
venv/bin/python -c "from app.api.deps.upload_rate_limit import check_upload_rate_limit; print('✓ Upload Limit OK')"
```

### Si las tablas no se crean:
```bash
ssh vps
cd /var/www/closecheck-api/backend
venv/bin/python << 'EOF'
from app.db.database import create_tables
create_tables()
print("✓ Tables created")
EOF
```

---

## Resumen

| Tarea | Estado | Quién | Cuándo |
|-------|--------|-------|--------|
| Código implementado | ✅ Completo | Copilot | Ya hecho |
| Tests locales | ✅ 34/34 passing | Copilot | Ya hecho |
| Variables agregadas a VPS | ✅ Hecho | Copilot | Ya hecho |
| CI/CD actualizado | ✅ Automático | Copilot | Ya hecho |
| **Restart servicio en VPS** | ⬜ **Pendiente** | **Tú** | Ahora |
| **Validar tests** | ⬜ **Pendiente** | **Tú** | Ahora |
| **Verificar tablas DB** | ⬜ **Pendiente** | **Tú** | Ahora |

**Una vez completes los 3 pasos manuales, todo estará listo para producción. ¿Necesitas ayuda con algo?**
