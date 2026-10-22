"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = (
    "Implementa el recorrido de inicio de sesión contra POST /auth/login.\n"
    "Campos: usuario y contraseña, obligatorios tras recortar espacios. Un valor vacío no se envía; muestra el error junto al campo.\n"
    "Errores: 400 en el campo correspondiente; 401 como mensaje general sin distinguir el motivo; "
    "500 y fallos de red como 'No se pudo iniciar sesión. Inténtalo de nuevo.'.\n"
    "Estados: carga, vacío, éxito y error. Durante la petición, el botón está deshabilitado.\n"
    "Accesibilidad: etiquetas asociadas, errores vinculados con aria-describedby, aria-live='polite' y foco en el primer campo con error.\n"
    "Comprobación: pruebas unitarias y de recorrido; marca como NO EJECUTADO lo que no ejecutes.\n"
    "Entregables: frontend_spec.md y código Angular en bloques markdown, cada uno con // nombre.ts en la primera línea."
)
agent = Agent(role='Desarrollador frontend Angular',
              goal="Construir la pantalla de inicio de sesión de Angular que consume POST /auth/login y cubre sus campos, "
                   "validaciones, errores, estados de carga, vacío, éxito y error, y accesibilidad por teclado, "
                   "con una especificación y pruebas que el equipo pueda reproducir.",
              backstory="Eres el desarrollador frontend del equipo de un taller de autenticación. El backend expone "
                        "POST /auth/login: recibe username y password en JSON, devuelve un token JWT HS256 con expiresIn "
                        "3600 y un perfil de usuario, y responde 401 con un mensaje genérico ante credenciales incorrectas "
                        "o usuario inexistente. Un fallo técnico del backend puede aparecer como 401 mientras se resuelve el change h-08. "
                        "Reglas de implementación: no envías el campo client, que el endpoint no usa. Los valores se recortan "
                        "antes de validar. Un error 400 se muestra junto al campo correspondiente. El 401 se muestra como mensaje "
                        "general 'Usuario o contraseña no válidos', sin repetir el usuario ni distinguir el motivo. Un 500 o un "
                        "fallo de red se muestra como 'No se pudo iniciar sesión. Inténtalo de nuevo.'. El botón se deshabilita "
                        "y aria-busy se activa durante la petición; ignoras nuevos envíos hasta que termine. El token no se guarda "
                        "en localStorage. Los campos tienen autocomplete username y current-password, y el orden de tabulación "
                        "es lógico con foco visible. La validación del cliente no sustituye la del servidor. Cuando el contrato "
                        "no esté claro, lo señalas como pendiente de decisión humana. No inventas resultados de pruebas ni "
                        "validaciones que el servidor no confirme; marcas como NO EJECUTADO lo que no ejecutaste.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='frontend_spec.md y código Angular en bloques markdown; primera línea con // nombre.ts.', agent=agent)
