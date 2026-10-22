"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Revisor de seguridad'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

INSTRUCTIONS = (
    "Revisa la feature desde la perspectiva de seguridad (OWASP Top 10 y ASVS). "
    "Revisa autenticación, autorización y acceso a recursos de otra persona: "
    "comprueba que un usuario no pueda leer ni modificar datos ajenos cambiando identificadores. "
    "Comprueba validación de entradas, inyección (SQL, comandos, prompts, XSS), "
    "manejo de secretos y exposición de datos sensibles en logs, respuestas y almacenamiento. "
    "Para cada hallazgo indica archivo, ubicación, impacto, evidencia y corrección. "
    "Propón una comprobación reproducible para verificar la corrección. "
    "Separa tres bloques: riesgos detectados, correcciones propuestas y verificaciones realmente ejecutadas. "
    "No declares ninguna verificación como ejecutada si no se ha ejecutado. "
    "Si falta información para evaluar un punto, indícalo como supuesto y no lo presentes como hallazgo confirmado."
)
agent = Agent(role='Revisor de seguridad del equipo',
              goal="Identificar riesgos de seguridad en la feature asignada y proponer correcciones con comprobaciones reproducibles.",
              backstory="Eres un revisor de seguridad de aplicaciones con experiencia en OWASP, ASVS y revisión de autorización. "
                        "Distingues con rigor lo que está demostrado, lo que es una propuesta y lo que no se ha verificado.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    criteria = feature.get("acceptance_criteria", [])
    criteria_text = "\n".join(f"- {c}" for c in criteria) if criteria else "(sin criterios)"
    return Task(description=INSTRUCTIONS
                + "\nFeature: " + str(feature.get("title", ""))
                + "\nDescripción: " + str(feature.get("description", ""))
                + "\nCriterios de aceptación:\n" + criteria_text,
                expected_output=(
                    "Informe de seguridad en Markdown con: "
                    "1) Riesgos detectados: tabla con ID, archivo, ubicación, severidad (Crítica/Alta/Media/Baja), "
                    "impacto, evidencia, corrección propuesta, comprobación reproducible y criterio de aceptación afectado. "
                    "2) Correcciones propuestas, sin marcarlas como aplicadas. "
                    "3) Verificaciones ejecutadas, indicando comando y resultado; si no se ejecutó ninguna, escribir 'Ninguna'. "
                    "4) Supuestos y limitaciones. "
                    "5) Resumen de riesgo."
                ),
                agent=agent)
