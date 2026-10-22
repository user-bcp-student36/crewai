"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = (
    "Implementa el recorrido de inicio de sesión según el contrato de API aprobado: POST /auth/login.\n"
    "Campos: usuario y contraseña, ambos obligatorios. Tras recortar espacios, un valor vacío no se envía; "
    "muestra el mensaje junto al campo y no hagas la petición. No envíes el campo client: el endpoint no lo usa.\n"
    "Errores de API: 400 (Username/Password is required) se muestra en el campo correspondiente; "
    "401 se muestra como mensaje general 'Usuario o contraseña no válidos', sin repetir el usuario ni distinguir el motivo; "
    "500 y fallos de red se muestran como 'No se pudo iniciar sesión. Inténtalo de nuevo.'.\n"
    "Estados: carga (botón deshabilitado y aria-busy mientras la petición está en curso), vacío (no hay petición), "
    "éxito (redirige o muestra confirmación; el token no se guarda en localStorage) y error (mensaje según el código anterior).\n"
    "Evita envíos duplicados: deshabilita el botón durante la petición e ignora nuevos envíos hasta que termine.\n"
    "Accesibilidad: etiqueta asociada a cada campo, aria-describedby para errores, aria-live='polite' para el mensaje general, "
    "foco en el primer campo con error, orden de tabulación lógico, foco visible, autocomplete username y current-password.\n"
    "La validación del cliente no sustituye la del servidor.\n"
    "Comprobación: describe pruebas unitarias y de recorrido (caso válido, cada error, doble envío, navegación por teclado). "
    "Marca como NO EJECUTADO cualquier resultado que no hayas ejecutado.\n"
    "Entregables: frontend_spec.md con campos, validaciones, acciones, mensajes, estados, accesibilidad y comprobación; "
    "y código Angular en bloques markdown, cada uno con // nombre.ts en la primera línea."
)
agent = Agent(role='Desarrollador frontend Angular',
              goal="Implementar el recorrido de inicio de sesión contra POST /auth/login con estados, validaciones y accesibilidad verificables.",
              backstory="Eres el desarrollador frontend del equipo. Conoces el contrato de API aprobado y sus errores, "
                        "y no inventas resultados de pruebas ni validaciones que el servidor no confirme.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='frontend_spec.md y código Angular en bloques markdown; primera línea con // nombre.ts.', agent=agent)
