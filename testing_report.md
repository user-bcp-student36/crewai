# Informe de pruebas

## Alcance y criterio de evidencia

Se verifican los contratos observables de este repositorio: normalización del backlog
MCP, manejo de errores de herramientas, extracción de criterios de aceptación,
persistencia del checkpoint y flujo de seis/siete roles con aprobación, rechazo y
reanudación. Los casos de integración del flujo usan dobles de prueba para Copilot,
GitHub Projects y la entrada humana; no contactan servicios externos.

Los fixtures de aceptación usan la funcionalidad ficticia **Transfer funds** como
datos controlados, no como una implementación bancaria real. No hay una API Quarkus
generada ni una base de datos de producto en este repositorio con la que validar
endpoints o migraciones ejecutables. Por tanto, cualquier prueba de integración con
un MCP/servidor real, API de producto o persistencia SQL de producto queda **NO
EJECUTADO**.

## Criterios de aceptación, pruebas y resultados esperados

| ID | Criterio de aceptación | Pruebas relacionadas | Resultado esperado | Resultado |
|---|---|---|---|---|
| AC-01 | La tarea de cada rol conserva título, descripción y todos los criterios de aceptación. | `WorkflowTests.test_each_role_builds_its_own_task` | Cada tarea contiene todos los datos de `FEATURE` y está asociada a su agente. | PASÓ |
| AC-02 | La API MCP de proyectos normaliza la respuesta del listado y los items, incluyendo formas alternativas de título/número. | `McpProjectsContractTests.test_list_projects_normalizes_api_shape`; `test_list_project_items_falls_back_when_filter_contract_rejected` | La forma pública queda normalizada y se usa `list_items` cuando ambas variantes de filtro son rechazadas. | PASÓ |
| AC-03 | Los errores de una herramienta MCP no deben parecer respuestas válidas; si falla cada variante de listado, se informa el fallo. | `McpProjectsContractTests.test_call_tool_raises_for_mcp_tool_error`; `test_list_project_items_raises_when_all_api_variants_fail` | `RuntimeError` contiene el error de MCP o informa que no se pudo listar; no se devuelve un backlog vacío como éxito. | PASÓ |
| AC-04 | El contrato de feature entrega título, descripción y criterios extraídos, incluidos los criterios vacíos y checkboxes. | `McpProjectsContractTests.test_acceptance_criteria_supports_checkboxes_and_empty_body`; `test_feature_contract_extracts_issue_fields` | Se devuelve el esquema `{title, description, acceptance_criteria}` y los criterios coinciden con el body. | PASÓ |
| AC-05 | Los pasos aprobados persisten y se recuperan desde checkpoint; un checkpoint JSON inválido no bloquea el arranque. | `WorkflowTests.test_checkpoint_round_trip_preserves_step_state`; `test_invalid_checkpoint_starts_with_empty_steps` | El round-trip conserva estado y salida; JSON inválido produce `{"steps": {}}`. | PASÓ |
| AC-06 | La aprobación guarda artefactos y checkpoint; una nueva ejecución reutiliza pasos ya aprobados. | `WorkflowTests.test_pipeline_saves_all_roles_and_resumes`; `test_seven_role_pipeline_saves_sql_passes_context_and_resumes` | Se guardan specs/código, el checkpoint queda aprobado y la segunda ejecución no repite llamadas al modelo. | PASÓ |
| AC-07 | Rechazar o reintentar la etapa de datos conserva la barrera humana, el feedback y evita ejecutar etapas posteriores antes de aprobar. | `WorkflowTests.test_data_retry_rejection_and_resume_keep_human_gate` | Se registra el rechazo, no aparece código posterior ni migración no aprobada; el reintento recibe feedback y la reanudación respeta aprobaciones. | PASÓ |
| AC-08 | El modo de siete roles es opt-in y valores de activación inválidos se rechazan. | `WorkflowTests.test_invalid_activation_is_rejected`; `WorkflowTests.test_seven_role_pipeline_saves_sql_passes_context_and_resumes` | `true` incluye Datos; `false` mantiene seis roles; cualquier valor distinto de true/false produce `ValueError`. | PASÓ |
| AC-09 | El contrato de checkpoint/spec y el flujo local se integran sin credenciales ni llamadas a servicios externos. | Todas las pruebas anteriores; `tools/verify.py` | La suite pasa localmente y no invoca Copilot, MCP real ni GitHub. | PASÓ |
| AC-10 | La integración real con el API MCP, endpoints Quarkus y una base de datos/migraciones se valida contra servicios disponibles. | Ejecución manual descrita abajo | API responde según su contrato y la migración crea/consulta datos según criterios del feature. | NO EJECUTADO |

## Casos detallados

Todos los casos automatizados crean sus datos en memoria o en directorios
temporales. La prueba de pipeline sustituye las dependencias externas y elimina su
directorio temporal automáticamente al terminar.

| Caso | Tipo | Preparación y datos | Pasos | Resultado esperado |
|---|---|---|---|---|
| TC-01 Criterios en las tareas | Positivo / integración local | Fixture `Transfer funds`, con descripción y criterio “Reject a transfer with insufficient funds”. | Construir tareas de los roles y revisar descripción/agente. | Cada rol recibe título, descripción y criterio. |
| TC-02 MCP `tools/list` | Positivo / contrato API | Simular resultado JSON-RPC con una herramienta `manage_project`. | Invocar `list_tools`. | Se retorna la lista y se invoca `tools/list` sin parámetros. |
| TC-03 Contenido de texto de herramienta | Positivo / contrato API | Simular `content` con JSON en texto; repetir con texto no JSON. | Invocar `call_tool`. | JSON se decodifica; texto ordinario se conserva como `{"raw": ...}`. |
| TC-04 Error MCP | Negativo / contrato API | Simular `isError: true` y mensaje `invalid project id`. | Invocar `call_tool`. | Se lanza `RuntimeError` con el error, no una respuesta exitosa vacía. |
| TC-05 Fallback del backlog | Negativo → positivo / integración de adaptador | Las llamadas `filter_items` (con `filter` y `filterQuery`) fallan; `list_items` retorna un issue con título/número. | Invocar `list_project_items("P1")`. | Se invocan tres variantes y se retorna el item normalizado. |
| TC-06 Todas las variantes MCP fallan | Negativo / integración de adaptador | Simular error en las tres formas de listar items. | Invocar `list_project_items("P1")`. | Se informa explícitamente `No se pudo listar items`; no se devuelve lista vacía como éxito. |
| TC-07 Criterios vacíos y checkboxes | Borde / contrato API | Body vacío y body markdown con checkboxes marcados/desmarcados. | Extraer criterios. | Vacío produce `[]`; ambas formas de checkbox producen el texto del criterio. |
| TC-08 Feature desde Issue | Positivo / contrato API | Simular Issue #42 con título y sección de criterios. | Invocar `get_feature(42)`. | Se retorna `{title, description, acceptance_criteria}` y se envía `issueNumber: 42`. |
| TC-09 Checkpoint guardado | Positivo / persistencia | Redirigir `CHECKPOINT_FILE` a un directorio temporal y guardar modo, feature y un paso aprobado. | Guardar y luego cargar el checkpoint. | Los datos se serializan como JSON UTF-8 y el round-trip conserva el estado. |
| TC-10 Checkpoint corrupto | Negativo / borde de persistencia | Escribir JSON mal formado en el checkpoint temporal. | Cargar el checkpoint. | Se inicia con `{"steps": {}}`, sin propagar el error JSON. |
| TC-11 Pipeline aprobado y reanudado | Positivo / integración local | Fixture del flujo, Copilot/MCP/selección/aprobación simulados, carpeta temporal. | Ejecutar `main()` y repetir con el checkpoint creado. | Artefactos y estado aprobado quedan persistidos; la segunda ejecución no vuelve a llamar al modelo. |
| TC-12 Rechazo/reintento de Datos | Negativo / integración local | Activar siete roles; rechazar el primer resultado, dar feedback en reintento y aprobar la siguiente ejecución. | Ejecutar flujo simulado en tres intentos controlados. | El rechazo se registra, no se ejecuta Backend antes de aprobar, y el feedback aparece en el prompt siguiente. |
| TC-13 Activación de Datos | Borde / configuración | Probar `CREWAI_INCLUDE_DATA=maybe`; probar además `true` y `false` en los flujos de integración. | Evaluar configuración y construir cada flujo. | Valor inválido da `ValueError`; los modos tienen siete y seis pasos respectivamente. |
| TC-14 Integración MCP/Quarkus/SQL real | Integración externa | Requiere endpoint MCP y backlog autorizados, artefactos de feature, Java/Maven y DB configurada. | Ejecutar los comandos de integración de la sección siguiente y verificar endpoints/migración contra criterios reales. | Contratos reales y persistencia cumplen el feature. | **NO EJECUTADO** |

## Preparación y comandos reproducibles

Desde la raíz del repositorio, en PowerShell:

```powershell
# Preparación, solo si aún no existe el entorno virtual
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Suite unitaria y de integración simulada
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Verificación estándar del repositorio (vuelve a ejecutar unittest)
.\.venv\Scripts\python.exe tools\verify.py
```

La suite no requiere `.env`, Copilot, GitHub, servicio MCP ni base de datos. No
configure credenciales reales para estos casos. Las pruebas utilizan mocks para
las respuestas MCP, Copilot y la aprobación del operador, y `TemporaryDirectory`
para checkpoints y artefactos.

### Integración real pendiente

Para validar un feature generado real, primero se requiere endpoint MCP y acceso
autorizado al backlog; después de ejecutar el Crew y revisar/aprobar sus artefactos:

```powershell
Set-Location output\backend-quarkus
mvn test
mvn compile quarkus:dev
```

En otra terminal, para el frontend:

```powershell
Set-Location output\frontend-angular
npm install
npm start
```

Estos comandos requieren que el feature ya haya generado backend/frontend y tests.
La API backend espera en `http://localhost:8080` y Angular en
`http://localhost:4200`. El contrato HTTP concreto, datos válidos/inválidos,
respuestas de error, migraciones, rollback y persistencia dependen de los criterios
del feature; no se inventan aquí. Para cada endpoint y operación de persistencia,
añadir casos con preparación, payload/registro, status/body o filas esperadas,
limpieza y evidencia real. **NO EJECUTADO** en esta entrega.

## Resultado de ejecución

Ejecuciones realizadas en Python 3.13.15. La rama de esta evidencia es
`agents/testing`.

| Comando | Resultado observado |
|---|---|
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | PASÓ — 16 pruebas en 0.235 s, `OK`. |
| `python tools\verify.py` | FALLÓ — ejecutó `C:\Program Files\Python313\python.exe`; unittest no pudo importar `requests` ni `crewai` (`ModuleNotFoundError`), por lo que reportó `Ran 2 tests ... FAILED (errors=2)` y `CalledProcessError` de salida 1. |
| `.\.venv\Scripts\python.exe tools\verify.py` | PASÓ — última repetición ejecutada con `C:\Users\Usuario\Documents\U23678-rosemarie-jeraly-medina-tello\crewai\.venv\Scripts\python.exe`; 16 pruebas en 0.127 s, `OK`; imprimió `All pipeline checks passed. No model or external service was called.` |
| Integración con MCP real, endpoint Quarkus y DB de producto | **NO EJECUTADO** — requiere endpoint, feature y contrato de API/persistencia concretos. |

La causa fue de entorno, no una regresión del agente: `tools/verify.py` reutiliza
`sys.executable` para lanzar unittest. Al invocarlo con `python` fuera del entorno
virtual, ambos módulos de prueba se ejecutaron con Python global, sin las
dependencias del proyecto. Activar `.venv` antes de correr `python tools/verify.py`
o invocar directamente `.\.venv\Scripts\python.exe tools\verify.py` resuelve el
problema; no hizo falta reinstalar dependencias en la validación de esta sesión.

Las pruebas de contrato MCP son unitarias: validan el adaptador contra respuestas
simuladas, no contra un servidor remoto. Las pruebas de integración de pipeline
mockean MCP/Copilot/entrada del operador. En consecuencia, el resultado positivo no
afirma disponibilidad o compatibilidad de servicios externos.

## Limpieza

- Los archivos temporales creados por las pruebas se eliminan automáticamente al
  salir de `TemporaryDirectory`.
- No se borran los artefactos preexistentes de `output/`.
- Para detener servidores iniciados durante la validación manual, usa `Ctrl+C` en
  sus respectivas terminales. El reporte no inicia ni detiene servicios externos.
