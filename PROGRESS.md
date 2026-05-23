# PROGRESS — Proyecto Integrador 1 (Consultorio Jurídico T4)

## Estado actual — 2026-05-23

### Completado ✅

- [x] **PASO 0 — Cloudinary**: configurado como storage de media. Rama `feat/cloudinary-setup` mergeada a `develop`.
- [x] **HU-22 — Grabar llamadas**: implementada. Ver detalles técnicos abajo.
- [x] **HU-23 — Acceso controlado a grabaciones**: implementada. 10 tests unitarios pasando.
- [x] **HU-24 — Métricas de canales**: view `communication_metrics` (solo admin), template con tarjetas + filtro + tabla. 13 tests unitarios pasando.
- [x] **Tests unitarios — HU-22, HU-23, HU-24**: 33 tests pasando, coverage >90% en archivos clave.
- [x] **Documentación DB**: `docs/modelo_de_datos.md` — todas las tablas, campos, índices, notas de seguridad.
- [x] **Casos de prueba**: `docs/samuel_hu_y_casos_de_prueba.md` — diseño de pruebas para sprint 3.
- [x] **Fix — Migración a WebRTC nativo**: VideoSDK reemplazado por WebRTC + Metered.ca.

---

## Qué funcionó y qué no (HU-22 / WebRTC)

### ❌ Lo que NO funcionó: VideoSDK

VideoSDK fue la solución original planificada en CLAUDE.md. Se implementó completo (token JWT, SDK JS, grabación con MediaRecorder), pero **nunca llegó a funcionar** porque:

- `call-api.videosdk.live` **no resuelve desde el ISP local**. La DNS no devuelve IP.
- Se intentó forzar con `/etc/hosts` (Windows: `C:\Windows\System32\drivers\etc\hosts`) apuntando a `13.229.56.241`, pero la conexión TCP a esa IP también timeout.
- Actualizar la versión del SDK JS de `0.0.67` a `0.0.87` tampoco ayudó — el problema es de red, no de versión.
- **Conclusión**: VideoSDK es inaccesible desde esta red. En producción (Render) podría funcionar, pero no se puede desarrollar ni probar localmente.

### ✅ Lo que SÍ funcionó: WebRTC nativo + Metered.ca

Se reemplazó VideoSDK con **WebRTC nativo del browser** (`RTCPeerConnection`) y **Metered.ca** para servidores STUN/TURN:

- **Señalización**: polling HTTP contra Django DB (`CallSession` model). No requiere WebSockets ni Channels.
- **Patrón Vanilla ICE**: se espera a que `iceGatheringState === 'complete'` antes de enviar el SDP (evita trickle ICE).
- **TURN servers**: Metered.ca free (50 GB/mes). API key en `.env`: `METERED_API_KEY` + `METERED_DOMAIN`.
- **Grabación**: `AudioContext` mezcla audio local + remoto → `MediaRecorder` graba → blob se sube a Django → Cloudinary vía `RawMediaCloudinaryStorage`.

### 🐛 Bugs encontrados y corregidos en WebRTC

| Bug | Causa | Fix |
|-----|-------|-----|
| `JSON.parse: unexpected character` | `get_ice_servers` tenía `@login_required`; callee no está autenticado → redirect 302 al login | Quitado `@login_required` de `get_ice_servers` |
| Callee no recibía la oferta | `join_webrtc_call` pasaba `offer_url=/oferta/` (endpoint POST del caller) en vez de `/oferta/leer/` (endpoint GET público) | Corregida la URL en el contexto del template |
| `BadRequest: Invalid image file` al subir grabación | `MediaCloudinaryStorage` intenta procesar el archivo webm como imagen | Cambiado `audio_file` a `storage=RawMediaCloudinaryStorage()` + migración `0006_audio_file_raw_storage` |

---

## Tests Selenium (HU-23 y HU-24)

### Estructura
```
cases/tests/selenium_tests/
├── features/
│   ├── environment.py        # Django ORM setup + before_all (crea usuarios con roles correctos)
│   ├── RecordingAccess.feature   # HU-23
│   ├── CommunicationMetrics.feature  # HU-24
│   └── steps/
│       ├── recording_access_steps.py
│       └── communication_metrics_steps.py
└── pages/
    ├── base_page.py
    ├── login_page.py
    ├── recording_access_page.py
    └── metrics_page.py
```

### Cómo correr
```bash
cd cases/tests/selenium_tests
python -m behave features/ --no-capture
```

**Prerequisito**: el servidor Django debe estar corriendo (`python manage.py runserver`).
**Los usuarios** `admin_selenium/selenium123` y `secretaria_selenium/selenium123` los crea automáticamente `environment.py` con los roles correctos.
**Las grabaciones**: el test HU-23 necesita al menos una interacción con `audio_file` en la DB. Se usa la primera disponible.

### Fixes aplicados (sesión anterior + sesión actual)
- `environment.py`: Django ORM setup en `before_all` — crea/verifica usuarios con `groups.set` (no `add`) para evitar contaminación de grupos
- `base_page.py`: `click` usa `element_to_be_clickable` + `scrollIntoView` para botones en headless
- `metrics_page.py`: selector de botón filtro cambiado a `form[method="get"] button[type="submit"]` (evita el botón de logout del sidebar); `filter_by_type` ahora espera que la URL contenga `tipo=<valor>` antes de retornar (fix de `StaleElementReferenceException`)
- `login_page.py`: espera que el browser salga de `/login` antes de retornar (evita race condition entre redirección y navegación del test)
- `recording_access_steps.py`: assertion de acceso denegado añade `'permiso'` al check; usa contexto dinámico para case_id e interaction_id
- `communication_metrics_steps.py`: assertion de secretaria verifica URL ≠ metrics URL; deprecación Selenium corregida

### Resultado final
```
2 features passed, 0 failed, 0 skipped
7 scenarios passed, 0 failed, 0 skipped
22 steps passed, 0 failed, 0 skipped
Took 0min 24.458s
```

---

## Última tarea completada

Todos los tests Selenium de HU-23 y HU-24 pasan (7/7). Fix final: `filter_by_type` en `metrics_page.py` espera que la URL cambie después de enviar el formulario, eliminando el `StaleElementReferenceException`.

---

## Siguiente paso

Los tests Selenium están completos. Opciones posibles:
1. Generar reporte HTML de coverage unitario: `pytest cases/tests/ --cov=cases --cov-report=html:docs/coverage_html`
2. Mergear `fix-uui-update` a `develop` (el usuario hace push manualmente)
3. Cerrar el sprint si no hay más tareas pendientes

---

## Branch activo

`fix-uui-update` — rama actual (pendiente merge a develop)

---

## Archivos tocados (WebRTC + HU-24 + Selenium fixes)

- `cases/models.py` — `CallSession` model, `RawMediaCloudinaryStorage` en `audio_file`
- `cases/views.py` — 7 vistas WebRTC + `communication_metrics` (HU-24) + fixes
- `cases/urls.py` — 8 URLs WebRTC + 1 HU-24
- `cases/migrations/0005_add_callsession_model.py`
- `cases/migrations/0006_audio_file_raw_storage.py`
- `templates/cases/case_detail.html` — UI caller WebRTC
- `templates/cases/call_room.html` — UI callee WebRTC
- `templates/cases/communication_metrics.html` — HU-24
- `cases/tests/test_hu22_recordings.py` — 10 tests ✅
- `cases/tests/test_hu23_recording_access.py` — 10 tests ✅
- `cases/tests/test_hu24_metrics.py` — 13 tests ✅
- `cases/tests/selenium_tests/features/environment.py` — Django setup + before_all
- `cases/tests/selenium_tests/features/steps/recording_access_steps.py`
- `cases/tests/selenium_tests/features/steps/communication_metrics_steps.py`
- `cases/tests/selenium_tests/pages/base_page.py` — click fix
- `cases/tests/selenium_tests/pages/metrics_page.py` — selector fix
- `docs/modelo_de_datos.md`
- `docs/samuel_hu_y_casos_de_prueba.md`
- `.env` — `METERED_API_KEY`, `METERED_DOMAIN`

---

## Variables de entorno necesarias

```
CLOUDINARY_CLOUD_NAME=dnqlslede
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
METERED_API_KEY=f18988561fca5ad697faddf7cf405201f78c
METERED_DOMAIN=burooficial.metered.live
```
