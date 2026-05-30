# HUs de Samuel Bonilla — Resumen y Diseño de Casos de Prueba

## Historial de HUs por sprint

| Sprint | HU | Descripción | Estado |
|--------|-----|-------------|--------|
| 1 | HU-12 | Restringir acceso a casos por rol | ✅ Completada |
| 1/2 | HU-31 | Control de acceso por roles | ✅ Completada |
| 1/2 | HU-7 | Asignación automática de casos a estudiante | ✅ Completada |
| 2 | HU-36 | Reporte de casos por sala jurídica | ✅ Completada |
| 2 | HU-37 | Reporte de casos por estado | ✅ Completada |
| 3 | HU-22 | Grabar llamadas desde la plataforma | ✅ Completada |
| 3 | HU-23 | Acceso controlado a grabaciones de llamadas | ✅ Completada |
| 3 | HU-24 | Métricas de canales de comunicación | ✅ Completada |

---

## Sprint 3 — Diseño de Pruebas Unitarias (PyTest)

### HU-22: Grabar llamadas desde la plataforma

**Archivo:** `cases/tests/test_hu22_recordings.py`

| ID | Escenario | Precondición | Entrada | Resultado esperado |
|----|-----------|--------------|---------|-------------------|
| U22-01 | Token VideoSDK se genera para usuario con permiso | Usuario autenticado como secretaria o estudiante asignado | GET `/casos/<id>/llamada/token/` | 200 + JSON `{token, roomId}` |
| U22-02 | Token no se genera sin login | Sin sesión activa | GET `/casos/<id>/llamada/token/` | 302 redirect a login |
| U22-03 | Subida de audio guarda interacción de tipo llamada | Caso existe, usuario tiene permiso | POST con archivo `.webm` | `CommunicationInteraction` creada con `audio_file` poblado |
| U22-04 | Subida sin archivo retorna 400 | Usuario autenticado | POST sin `audio` en body | 400 + `{error: 'No se recibió archivo de audio'}` |
| U22-05 | Subida registra en CaseAuditLog | Caso existe | POST con audio válido | `CaseAuditLog` con action=`COMMUNICATION` creado |
| U22-06 | Error en subida registra en CaseAuditLog | Fallo en storage | POST con audio | `CaseAuditLog` con descripción del error |
| U22-07 | Secretaria sin permiso no puede subir | Usuario secretaria | POST a upload | 403 |
| U22-08 | Endpoint ICE servers retorna lista de servidores | METERED_API_KEY en `.env` | GET `/casos/<id>/webrtc/ice/` | 200 + `{iceServers: [...]}` |
| U22-09 | Crear sesión crea CallSession en BD | Usuario autenticado | POST `/casos/<id>/webrtc/crear/` | 201 + `{roomId}`, objeto `CallSession` en DB |
| U22-10 | Callee puede leer oferta sin estar autenticado | Caller ya envió oferta | GET `/casos/<id>/webrtc/<room>/oferta/leer/` | 200 + `{offer: {...}}` |

### HU-23: Acceso controlado a grabaciones de llamadas

**Archivo:** `cases/tests/test_hu23_recording_access.py`

| ID | Escenario | Precondición | Entrada | Resultado esperado |
|----|-----------|--------------|---------|-------------------|
| U23-01 | Administrador puede acceder a grabación | Interacción con `audio_file` | GET `/grabaciones/<id>/` | 200 o 302 a URL de audio |
| U23-02 | Profesor puede acceder a grabación | Interacción con `audio_file` | GET `/grabaciones/<id>/` | 200 o 302 a URL de audio |
| U23-03 | Secretaria no puede acceder | Usuario secretaria autenticado | GET `/grabaciones/<id>/` | 403 |
| U23-04 | Estudiante asignado al caso puede acceder | `assigned_student == request.user` | GET `/grabaciones/<id>/` | 200 o 302 a URL de audio |
| U23-05 | Estudiante no asignado no puede acceder | `assigned_student != request.user` | GET `/grabaciones/<id>/` | 403 |
| U23-06 | Sin login redirige a login | Sin sesión | GET `/grabaciones/<id>/` | 302 a `/login/` |
| U23-07 | Interacción sin audio retorna 404 | `audio_file` vacío | GET `/grabaciones/<id>/` | 404 |
| U23-08 | Acceso denegado registra en CaseAuditLog | Secretaria intenta acceder | GET `/grabaciones/<id>/` | `CaseAuditLog` action=`SECURITY_DENIED` |
| U23-09 | Template muestra candado para secretaria | Secretaria en detalle del caso | GET `/casos/<id>/` | HTML contiene `bi-lock-fill` |
| U23-10 | Template muestra reproductor para admin | Admin en detalle del caso | GET `/casos/<id>/` | HTML contiene `<audio controls` |

### HU-24: Métricas de canales de comunicación

**Archivo:** `cases/tests/test_hu24_metrics.py`

| ID | Escenario | Precondición | Entrada | Resultado esperado |
|----|-----------|--------------|---------|-------------------|
| U24-01 | Administrador puede ver métricas | Usuario administrador | GET `/casos/metricas/comunicaciones/` | 200 + template `communication_metrics.html` |
| U24-02 | Profesor no puede acceder | Usuario profesor | GET `/casos/metricas/comunicaciones/` | 403 o redirect |
| U24-03 | Secretaria no puede acceder | Usuario secretaria | GET `/casos/metricas/comunicaciones/` | 403 o redirect |
| U24-04 | Estudiante no puede acceder | Usuario estudiante | GET `/casos/metricas/comunicaciones/` | 403 o redirect |
| U24-05 | Sin login redirige | Sin sesión | GET `/casos/metricas/comunicaciones/` | 302 a `/login/` |
| U24-06 | Métricas agrupan correctamente por canal | 2 llamadas + 1 mensaje registrados | GET sin filtro | `metrics` contiene `llamada:2`, `mensaje:1` |
| U24-07 | Total es suma de todas las interacciones | N interacciones en DB | GET sin filtro | `total == N` |
| U24-08 | Filtro por canal retorna solo ese tipo | Mezcla de tipos | GET `?tipo=llamada` | Todas las `interactions` son tipo `llamada` |
| U24-09 | Sin filtro retorna todas las interacciones | 2 interacciones de tipos distintos | GET sin `tipo` | `interactions.count() == 2` |
| U24-10 | Sin interacciones muestra total cero | DB vacía | GET | `total == 0`, `metrics` vacío |
| U24-11 | Template muestra tarjetas por canal | Al menos 1 interacción | GET | HTML contiene el label del canal |
| U24-12 | Template muestra filtro | Siempre | GET | HTML contiene "Filtrar por canal" |
| U24-13 | `tipo_choices` en contexto del template | Siempre | GET | `tipo_choices == CommunicationInteraction.TYPE_CHOICES` |

---

## Sprint 3 — Diseño de Pruebas Funcionales Selenium (Behave)

### HU-22: Grabar llamadas

**Feature:** `cases/tests/selenium_tests/features/RecordCall.feature`

```gherkin
Feature: Grabación de llamadas desde la plataforma

  Scenario: Abrir sala de llamada como caller
    Given El usuario está autenticado como secretaria
    When Ingresa al detalle de un caso
    And Hace clic en "Iniciar llamada"
    Then Se muestra el link de sala para compartir
    And El estado muestra "Esperando participante…"

  Scenario: Colgar y guardar grabación
    Given El usuario está en una llamada activa como caller
    When Hace clic en "Colgar y guardar grabación"
    Then Se muestra "Guardando grabación..."
    And Luego aparece "Grabación guardada correctamente"

  Scenario: La grabación aparece en el historial de interacciones
    Given Se acaba de guardar una grabación
    When El usuario recarga la página del caso
    Then Aparece una interacción de tipo "Llamada" con reproductor de audio
```

### HU-23: Acceso controlado a grabaciones

**Feature:** `cases/tests/selenium_tests/features/RecordingAccess.feature`

```gherkin
Feature: Acceso controlado a grabaciones de llamadas

  Scenario: Administrador puede reproducir grabación
    Given Existe una interacción de llamada con grabación
    And El usuario está autenticado como administrador
    When Ingresa al detalle del caso
    Then Puede ver el reproductor de audio <audio controls>

  Scenario: Secretaria ve candado en lugar del reproductor
    Given Existe una interacción de llamada con grabación
    And El usuario está autenticado como secretaria
    When Ingresa al detalle del caso
    Then Ve el ícono de candado y el mensaje de acceso restringido
    And No ve ningún reproductor de audio

  Scenario: Secretaria no puede acceder a URL de grabación directamente
    Given Existe una interacción de llamada con grabación
    And El usuario está autenticado como secretaria
    When Intenta acceder a /grabaciones/<id>/ directamente
    Then Obtiene un error 403
```

### HU-24: Métricas de canales

**Feature:** `cases/tests/selenium_tests/features/CommunicationMetrics.feature`

```gherkin
Feature: Métricas de canales de comunicación

  Scenario: Administrador ve métricas de canales
    Given El usuario está autenticado como administrador
    And Existen interacciones de distintos tipos en el sistema
    When Ingresa a /casos/metricas/comunicaciones/
    Then Ve tarjetas con el conteo por canal
    And Ve la tabla de últimas 100 interacciones

  Scenario: Filtrar métricas por canal específico
    Given El usuario está en la vista de métricas
    And Existen interacciones de tipo "llamada" y "mensaje"
    When Selecciona "Llamada" en el filtro y hace clic en Filtrar
    Then La tabla solo muestra interacciones de tipo Llamada

  Scenario: Limpiar filtro muestra todas las interacciones
    Given El usuario filtró por "llamada"
    When Hace clic en "Limpiar"
    Then La tabla vuelve a mostrar todos los tipos

  Scenario: Rol no autorizado no puede ver métricas
    Given El usuario está autenticado como secretaria
    When Intenta ingresar a /casos/metricas/comunicaciones/
    Then Es redirigido o recibe error de acceso denegado
```

---

## Coverage de pruebas unitarias

Para generar el reporte de coverage:
```bash
pytest cases/tests/test_hu22_recordings.py cases/tests/test_hu23_recording_access.py cases/tests/test_hu24_metrics.py --cov=cases --cov-report=term-missing -v
```
