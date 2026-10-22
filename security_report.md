# Informe de revisión de seguridad

## 1. Alcance

Revisión del código del workspace `crewai` en cuatro ejes:

- Autenticación y autorización, incluido el acceso a recursos de otra persona (owner/repo ajenos).
- Validación de entradas e inyección (argumentos de scripts, prompts, código generado, rutas de escritura).
- Gestión de secretos y configuración (`.env`, tokens de GitHub, claves MCP, versionado).
- Exposición de datos sensibles (red, logs, checkpoints, servicio externo de modelo).

Fuera de alcance: ejecución de los servicios Docker/Podman, pruebas contra GitHub real, y análisis de las aplicaciones Quarkus/Angular generadas en tiempo de ejecución.

## 2. Metodología

- Lectura estática de los archivos: [main.py](main.py), [mcp_projects.py](mcp_projects.py), [lab_copilot/runtime.py](lab_copilot/runtime.py), [crew/llm_config.py](crew/llm_config.py), [crew/workflow.py](crew/workflow.py), [support/mcp-local/compose.yaml](support/mcp-local/compose.yaml), [support/mcp-local/Dockerfile](support/mcp-local/Dockerfile), [support/mcp-local/start-mcp.sh](support/mcp-local/start-mcp.sh), [support/mcp-local/start-mcp.ps1](support/mcp-local/start-mcp.ps1), [.gitignore](.gitignore) y [.env.example](.env.example).
- Búsqueda de patrones peligrosos (`eval`, `exec`, `pickle`, `yaml.load`, `shell=True`, `verify=False`, claves y tokens) en el código Python.
- Escaneo de secretos sobre los archivos versionados (`git ls-files`).
- Ejecución de la batería de pruebas del proyecto (`tools/verify.py`).

## 3. Resumen

| ID | Severidad | Título | Estado |
|----|-----------|--------|--------|
| F-01 | Alta | Servicios MCP publicados en todas las interfaces | Riesgo detectado |
| F-02 | Alta | Token OAuth de `gh` con alcance amplio inyectado en contenedores | Riesgo detectado |
| F-03 | Media | Autorización por recurso ausente: owner/repo se usan sin lista permitida | Riesgo detectado |
| F-04 | Media | Clave MCP y transporte HTTP en claro por defecto | Riesgo detectado |
| F-05 | Media | Validación inconsistente de `Owner`/`Repo` en PowerShell | Riesgo detectado |
| F-06 | Media | Código generado por el modelo se escribe sobre archivos existentes | Riesgo detectado (mitigado por HITL) |
| F-07 | Media | Inyección de prompt desde backlog y feedback humano | Riesgo detectado (mitigado parcialmente) |
| F-08 | Media | Datos del proyecto enviados a un servicio externo y guardados en claro | Riesgo detectado |
| F-09 | Baja | Clave vacía enviada como `Bearer` sin fallar | Riesgo detectado |
| F-10 | Baja | Configuración de la app generada: SQL logging y CORS sin perfiles | Riesgo detectado |
| F-11 | Baja | TypeScript con `strict: false` en la plantilla Angular | Riesgo detectado |
| F-12 | Baja | Cadena de suministro: imágenes y dependencias sin versión fijada | Riesgo detectado |
| F-13 | Informativa | `GITHUB_OWNER` en `.env` con longitud anómala | Pendiente de revisión manual |

Controles correctos verificados: `.env` no está versionado ni tiene historial (ver sección 5).

## 4. Hallazgos

### F-01. Servicios MCP publicados en todas las interfaces (Alta)

- Archivo y ubicación: [support/mcp-local/compose.yaml](support/mcp-local/compose.yaml#L11) (`"8083:8080"`) y [support/mcp-local/compose.yaml](support/mcp-local/compose.yaml#L22) (`"8081:8080"`).
- Evidencia: el mapeo sin IP de host hace que Docker/Podman escuche en `0.0.0.0`. El proxy `mcp-proxy` ([support/mcp-local/Dockerfile](support/mcp-local/Dockerfile#L7)) se arranca con `--server stream` sin autenticación propia; la única barrera es la clave Bearer validada por el servidor, que no está en este repositorio.
- Impacto: cualquier equipo de la misma red puede llamar a la API de proyectos/tareas con el token de GitHub inyectado (ver F-02). Sin TLS, la clave viaja en claro.
- Corrección propuesta: publicar solo en loopback.

  ```yaml
  ports:
    - "127.0.0.1:8081:8080"
    - "127.0.0.1:8083:8080"
  ```

- Comprobación reproducible (no ejecutada):
  1. `docker compose -f support/mcp-local/compose.yaml config` debe mostrar `host_ip: 127.0.0.1`.
  2. Desde otro equipo de la red: `Test-NetConnection -ComputerName <IP_LAN> -Port 8081` debe fallar.

### F-02. Token OAuth de `gh` con alcance amplio inyectado en contenedores (Alta)

- Archivo y ubicación: [support/mcp-local/start-mcp.sh](support/mcp-local/start-mcp.sh#L30) (`LAB4_GITHUB_TOKEN=$(gh auth token)`) y [support/mcp-local/start-mcp.sh](support/mcp-local/start-mcp.sh#L32) (`export GITHUB_TOKEN=...`); [support/mcp-local/start-mcp.ps1](support/mcp-local/start-mcp.ps1#L51) y [support/mcp-local/start-mcp.ps1](support/mcp-local/start-mcp.ps1#L60); inyección en [support/mcp-local/compose.yaml](support/mcp-local/compose.yaml#L5) y [support/mcp-local/compose.yaml](support/mcp-local/compose.yaml#L16).
- Evidencia: el token es la sesión OAuth completa del usuario, no un token acotado. Se pasa como variable de entorno al contenedor.
- Impacto: un fallo en el contenedor o en el proxy expone acceso amplio a todas las cuentas y repositorios del usuario. Las variables de entorno son visibles con `docker inspect`.
- Corrección propuesta: usar un token de grano fino (fine-grained PAT) limitado al repositorio y a los permisos mínimos; pasarlo como secreto de Compose (archivo con permisos restringidos) en lugar de variable de entorno.

  ```yaml
  services:
    github-task:
      secrets:
        - github_token
  secrets:
    github_token:
      file: ./secrets/github_token.txt   # fuera de Git, permisos 600
  ```

- Comprobación reproducible (no ejecutada): `docker inspect <contenedor> --format "{{range .Config.Env}}{{println .}}{{end}}"` no debe listar `GITHUB_TOKEN` tras la corrección.

### F-03. Autorización por recurso ausente: owner/repo se usan sin lista permitida (Media)

- Archivo y ubicación: [mcp_projects.py](mcp_projects.py#L200) (`_OWNER`, `_REPO` desde `.env`); [support/mcp-local/start-mcp.sh](support/mcp-local/start-mcp.sh#L19) acepta cualquier `owner` que cumpla el formato; [support/mcp-local/start-mcp.ps1](support/mcp-local/start-mcp.ps1#L2) acepta cualquier valor.
- Evidencia: el código no comprueba que el owner/repo sea el previsto del alumno. El token del usuario sirve para cualquier repositorio al que tenga acceso, incluidos los de otra persona (por ejemplo, un repositorio del profesor o de otro alumno).
- Impacto: operaciones de lectura y escritura sobre recursos ajenos con credenciales propias.
- Corrección propuesta: lista permitida de owner/repo en la carga de configuración y falla explícita si no coincide.

  ```python
  ALLOWED = {("mi-usuario", "mi-repo")}
  if (_OWNER, _REPO) not in ALLOWED:
      raise RuntimeError("Owner/repo no autorizado para este laboratorio")
  ```

- Comprobación reproducible (no ejecutada): con `GITHUB_OWNER=otro` la carga debe fallar antes de cualquier llamada HTTP.

### F-04. Clave MCP y transporte HTTP en claro por defecto (Media)

- Archivo y ubicación: [mcp_projects.py](mcp_projects.py#L17) (`http://localhost:8081` por defecto).
- Evidencia: la URL por defecto y la del `.env` usan `http://`. La clave Bearer se envía en la cabecera de cada petición. No hay comprobación de esquema.
- Impacto: si `PROJECTS_MCP_URL` apunta a un host remoto, la clave viaja en claro.
- Corrección propuesta: exigir `https://` salvo que el host sea `localhost` o `127.0.0.1`.
- Comprobación reproducible (no ejecutada): test unitario con `PROJECTS_MCP_URL=http://10.0.0.5:8081` que espera excepción.

### F-05. Validación inconsistente de `Owner`/`Repo` en PowerShell (Media)

- Archivo y ubicación: [support/mcp-local/start-mcp.ps1](support/mcp-local/start-mcp.ps1#L2-L3) (sin `ValidatePattern`); [support/mcp-local/start-mcp.sh](support/mcp-local/start-mcp.sh#L19-L20) sí valida con expresión regular.
- Evidencia: los valores por defecto `OWNER` y `REPO` se aceptan sin error y se exportan a `GITHUB_OWNER`/`GITHUB_REPO` ([start-mcp.ps1](support/mcp-local/start-mcp.ps1#L61-L62)).
- Impacto: valores mal formados llegan al entorno del contenedor; los placeholders permiten arrancar un servicio mal configurado.
- Corrección propuesta:

  ```powershell
  [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9-]*$')][string]$Owner = "OWNER",
  [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Repo = "REPO",
  ```

  Además, rechazar los valores `OWNER` y `REPO` tal como hace el script de bash con el texto de ayuda.
- Comprobación reproducible (no ejecutada): `.\support\mcp-local\start-mcp.ps1 -Owner 'a;b'` debe terminar con error antes de llamar a `gh`.

### F-06. Código generado por el modelo se escribe sobre archivos existentes (Media)

- Archivo y ubicación: [main.py](main.py#L463) (`extract_and_save_code`), con la selección de nombre en [main.py](main.py#L526) y la escritura en [main.py](main.py#L590).
- Evidencia: el nombre de archivo lo propone el modelo. Se toma solo el nombre base (`Path(...).name`), lo que impide el salto de directorio (no se encontraron rutas con `..` que escapen de `OUTPUT_DIR`). Sin embargo, `write_text` sobrescribe cualquier archivo existente, incluidos los andamiajes como `pom.xml` o `application.properties` que se generan en [main.py](main.py#L364-L370).
- Impacto: una salida del modelo puede reemplazar archivos de andamiaje o de pasos aprobados.
- Mitigación actual: la escritura ocurre tras la aprobación humana ([main.py](main.py#L784), [main.py](main.py#L812)).
- Corrección propuesta: no sobrescribir los archivos de andamiaje, o registrar un hash y pedir confirmación.
- Comprobación reproducible (no ejecutada): llamar a `extract_and_save_code` con un bloque `// ../../pom.xml` y un directorio temporal como `OUTPUT_DIR`; no debe escribir fuera de él ni reemplazar `pom.xml`.

### F-07. Inyección de prompt desde backlog y feedback humano (Media)

- Archivo y ubicación: el feedback humano se inserta en la descripción de la tarea dentro de [main.py](main.py#L866) (bloque "FEEDBACK HUMANO"); el texto de la feature viene de GitHub ([mcp_projects.py](mcp_projects.py)).
- Evidencia: la descripción de la feature (que cualquiera con acceso al tablero puede editar) y el feedback se concatenan sin delimitar al prompt.
- Mitigación parcial: [lab_copilot/runtime.py](lab_copilot/runtime.py#L39) usa `available_tools=[]` y [lab_copilot/runtime.py](lab_copilot/runtime.py#L31) rechaza todos los permisos. El modelo no puede ejecutar herramientas, pero puede generar código malicioso que llegue a los archivos si el revisor humano no lo detecta.
- Corrección propuesta: delimitar la entrada no confiable en el prompt, limitar su longitud y mantener la revisión humana obligatoria.
- Comprobación reproducible (no ejecutada): revisión manual de una feature con instrucciones del tipo "ignora lo anterior y escribe X" y verificar que el paso de revisión la marca.

### F-08. Datos del proyecto enviados a un servicio externo y guardados en claro (Media)

- Archivo y ubicación: [lab_copilot/runtime.py](lab_copilot/runtime.py#L34-L44) envía el prompt completo y `working_directory=os.getcwd()`; [main.py](main.py#L438-L456) guarda todas las salidas en `output/.checkpoint.json`.
- Evidencia: el checkpoint contiene el texto completo de cada agente, sin cifrado ni permisos restringidos.
- Mitigación: [.gitignore](.gitignore#L1) excluye `.env`, `.env.*` y `output/`.
- Impacto: fuga de datos del proyecto al servicio del modelo y, en equipos compartidos, a otros usuarios locales.
- Corrección propuesta: documentar qué datos se envían; no incluir datos reales de terceros en el backlog; revisar permisos del checkpoint.
- Comprobación reproducible (no ejecutada): tras una ejecución, `Select-String -Path output\.checkpoint.json -Pattern 'password|token|secret'` debe devolver cero coincidencias.

### F-09. Clave vacía enviada como `Bearer` sin fallar (Baja)

- Archivo y ubicación: [mcp_projects.py](mcp_projects.py#L18) (`_KEY = os.getenv("PROJECTS_MCP_API_KEY", "")`).
- Impacto: si la variable falta, la petición sale con `Authorization: Bearer ` vacío y el error llega tarde y poco claro.
- Corrección propuesta: `if not _KEY: raise RuntimeError("Falta PROJECTS_MCP_API_KEY")`.
- Comprobación reproducible (no ejecutada): ejecutar con la variable sin definir y esperar la excepción.

### F-10. Configuración de la app generada: SQL logging y CORS sin perfiles (Baja)

- Archivo y ubicación: [main.py](main.py#L180-L181) (CORS con orígenes de `localhost`); [main.py](main.py#L187-L189) (H2 en memoria, `drop-and-create`, `log.sql=true`).
- Impacto: las sentencias SQL con datos personales aparecen en los logs; la configuración de desarrollo puede pasar a producción.
- Corrección propuesta: `quarkus.hibernate-orm.log.sql=false` y separar la configuración en perfiles `%dev` y `%prod`.
- Comprobación reproducible (no ejecutada): `grep "log.sql" application.properties` en la salida generada debe mostrar `%dev` o `false` fuera de desarrollo.

### F-11. TypeScript con `strict: false` en la plantilla Angular (Baja)

- Archivo y ubicación: [main.py](main.py#L279) (`"strict": false`).
- Impacto: menor comprobación de tipos y de valores nulos en el código generado.
- Corrección propuesta: `"strict": true`.
- Comprobación reproducible (no ejecutada): `npx tsc --noEmit` en el frontend generado con `strict` activado.

### F-12. Cadena de suministro: imágenes y dependencias sin versión fijada (Baja)

- Archivo y ubicación: [support/mcp-local/Dockerfile](support/mcp-local/Dockerfile#L1) (`:latest`), [support/mcp-local/Dockerfile](support/mcp-local/Dockerfile#L7) (`npm install -g mcp-proxy` sin versión); [main.py](main.py#L97) (Quarkus 3.8.3, versión antigua); [main.py](main.py#L143) (`jbcrypt`, biblioteca antigua y poco mantenida); [requirements.txt](requirements.txt) con rangos `>=`.
- Impacto: builds no reproducibles y posibles vulnerabilidades conocidas sin corregir.
- Corrección propuesta: fijar versiones y digests, usar un lock file para Python, comprobar CVEs con `pip-audit` y el plugin de OWASP para Maven, y valorar la alternativa a `jbcrypt` que ofrezca Quarkus.
- Comprobación reproducible (no ejecutada): `pip-audit -r requirements.txt`.

### F-13. `GITHUB_OWNER` en `.env` con longitud anómala (Informativa)

- Archivo: `.env` (local, no versionado). El valor no se muestra en este informe.
- Evidencia: el valor tiene 55 caracteres. Un nombre de usuario u organización de GitHub admite como máximo 39.
- Acción: revisar manualmente que sea solo el nombre de la cuenta y no una URL, un token u otro dato sensible.

## 5. Controles verificados (correctos)

- `.env` está ignorado por Git (`.gitignore:1`) y no está versionado ni tiene historial de commits.
- `.env.example` solo contiene placeholders (`prj-xxxxxxxxxxxxxxxxxxxx`).
- `lab_copilot/runtime.py` deniega las solicitudes de permiso y no expone herramientas al modelo.
- `main.py` no usa `eval`, `exec`, `pickle` ni `yaml.load`; los `subprocess` están solo en `tools/verify.py` con argumentos fijos.
- TLS está activo por defecto en `requests` (no se desactiva con `verify=False`).

## 6. Riesgos detectados, correcciones propuestas y verificaciones ejecutadas

### 6.1 Verificaciones realmente ejecutadas

| Verificación | Comando | Resultado |
|--------------|---------|-----------|
| Batería de pruebas del proyecto | `python tools/verify.py` | OK. 5 tests ejecutados (`Ran 5 tests`), 0 fallos, 0 errores. Incluye el paso con aprobación humana, reintentos, reanudación desde checkpoint y la validación de activación inválida. No cubre directamente [agents/security.py](agents/security.py). |
| Escaneo de secretos en archivos versionados | Patrones de GitHub PAT, OAuth, claves OpenAI/AWS y claves privadas sobre `git ls-files` | Sin coincidencias reales. La única coincidencia es el placeholder de [.env.example](.env.example). |
| Estado de `.env` | `git check-ignore -v .env`, `git ls-files .env`, `git log --all -- .env` | Ignorado por `.gitignore:1`, no versionado, sin historial. |

### 6.2 Correcciones propuestas (no aplicadas)

Ninguna corrección de código se ha aplicado en esta revisión. Las correcciones de F-01 a F-12 están descritas en la sección 4 y requieren aprobación antes de implementarlas.

### 6.3 Verificaciones pendientes (no ejecutadas)

Las comprobaciones de F-01, F-02, F-03, F-04, F-05, F-06, F-08, F-09, F-10, F-11 y F-12 están descritas como comandos o pruebas en la sección 4. Ninguna se ha ejecutado. Requieren los servicios Docker/Podman en marcha, la configuración de red, o pruebas unitarias nuevas que aún no existen.

## 7. Limitaciones

- Revisión estática: no se levantaron los contenedores ni se hicieron peticiones reales a GitHub ni al servicio MCP.
- La lógica de autenticación del servidor MCP no está en este repositorio; F-01 y F-04 dependen de ella.
- La seguridad de las aplicaciones Quarkus y Angular generadas por el modelo no se evaluó en tiempo de ejecución.
- El archivo [agents/security.py.bak](agents/security.py.bak) es una copia de seguridad del agente original y puede eliminarse si ya no se necesita.
