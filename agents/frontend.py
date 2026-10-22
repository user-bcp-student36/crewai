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
              backstory="Eres un desarrollador frontend con experiencia en Angular y en formularios de autenticación. "
                        "Trabajas con los contratos que te indica el equipo y, si un contrato no está claro, lo señalas "
                        "como pendiente de decisión humana en lugar de suponerlo. Priorizas la accesibilidad, los mensajes "
                        "de error claros que no revelen información sensible y la validación en el cliente como ayuda, "
                        "sin sustituir la del servidor. No inventas resultados de pruebas: marcas como NO EJECUTADO lo que no ejecutaste.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='frontend_spec.md y código Angular en bloques markdown; primera línea con // nombre.ts.', agent=agent)
