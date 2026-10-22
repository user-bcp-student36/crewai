"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Revisor de seguridad'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

ROLE = 'Revisor de seguridad'
GOAL = "Identificar riesgos de seguridad en la feature asignada y proponer correcciones con comprobaciones reproducibles."
BACKSTORY = (
    "Revisor de seguridad de aplicaciones con experiencia en OWASP ASVS y revisión de autorización. "
    "Distingues lo demostrado, lo propuesto y lo no verificado."
)
INSTRUCTIONS = """Revisa autenticación, autorización y acceso a recursos de otra persona del Issue del equipo.
Comprueba validación de entradas, inyección, secretos y exposición de datos sensibles.
Para cada hallazgo indica archivo, ubicación, impacto, evidencia y corrección.
Propón una comprobación reproducible de la corrección.
Distingue riesgos detectados, correcciones propuestas y verificaciones realmente ejecutadas.
Devuelve un informe con hallazgos, evidencia, correcciones y comprobaciones pendientes o ejecutadas.
Si un punto carece de evidencia, indícalo como supuesto y no como hallazgo."""
EXPECTED_OUTPUT = (
    "Informe Markdown con tres secciones: riesgos detectados (archivo, ubicación, severidad, "
    "impacto, evidencia, corrección y comprobación reproducible), correcciones propuestas y "
    "verificaciones ejecutadas (comando y resultado; 'Ninguna' si no se ejecutó nada). "
    "Cierra con supuestos y un resumen de riesgo."
)
agent = Agent(role=ROLE, goal=GOAL, backstory=BACKSTORY,
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    criteria = feature.get("acceptance_criteria", [])
    criteria_text = "\n".join(f"- {c}" for c in criteria) if criteria else "(sin criterios)"
    return Task(description=INSTRUCTIONS
                + "\nFeature: " + str(feature.get("title", ""))
                + "\nDescripción: " + str(feature.get("description", ""))
                + "\nCriterios de aceptación:\n" + criteria_text,
                expected_output=EXPECTED_OUTPUT,
                agent=agent)
