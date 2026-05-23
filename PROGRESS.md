# PROGRESS — Proyecto Integrador 1 (Consultorio Jurídico T4)

## Estado actual — 2026-05-23

### Completado ✅

- [x] **PASO 0 — Cloudinary**: configurado como storage de media. Rama `feat/cloudinary-setup` mergeada a `develop`.
- [x] **HU-22 — Grabar llamadas**: implementada. Ver detalles técnicos abajo.
- [x] **HU-23 — Acceso controlado a grabaciones**: implementada. 10 tests unitarios pasando.
- [x] **Fix — Migración a WebRTC nativo**: VideoSDK reemplazado por WebRTC + Metered.ca. Rama `fix/webrtc-nativo` activa (pendiente merge a develop).

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

## Última tarea completada

Fix del storage de audio: `audio_file` en `CommunicationInteraction` ahora usa `RawMediaCloudinaryStorage` en vez de `MediaCloudinaryStorage`. Grabaciones de llamadas (.webm) se suben correctamente a Cloudinary.

---

## Siguiente paso

**Mergear `fix/webrtc-nativo` a `develop`**, luego:
1. Crear rama desde `develop` para HU-24 (o recuperar stash de `feat/hu-24-metricas-canales`)
2. Implementar `communication_metrics` view (ya existe parcialmente)
3. Escribir tests unitarios HU-24
4. Mergear a `develop`

---

## Branch activo

`fix/webrtc-nativo` — pendiente merge a develop

---

## Archivos tocados (WebRTC + fixes)

- `cases/models.py` — `CallSession` model, `RawMediaCloudinaryStorage` en `audio_file`
- `cases/views.py` — 7 vistas WebRTC, fix `@login_required`, fix `offer_url`
- `cases/urls.py` — 8 URLs WebRTC
- `cases/migrations/0005_add_callsession_model.py`
- `cases/migrations/0006_audio_file_raw_storage.py`
- `templates/cases/case_detail.html` — UI caller WebRTC (reemplaza VideoSDK)
- `templates/cases/call_room.html` — UI callee WebRTC (reemplaza VideoSDK)
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

---

## Pendiente (Sprint 3)

- [ ] HU-24 — Métricas de canales: view + template + tests unitarios + tests Selenium
- [ ] Tests Selenium HU-22 y HU-23
- [ ] Actualizar `.env.example` con las variables de Metered.ca
- [ ] Merge `fix/webrtc-nativo` → `develop`
