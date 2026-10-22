"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = (
    "Entrega chapter_review.md con VEREDICTO: APROBADO o RECHAZADO, motivos y correcciones."
)

agent = Agent(role='Chapter',
              goal="Revisar de forma integral la entrega de una funcionalidad. Contrasta cada criterio de aceptación con arquitectura, persistencia, implementación, pruebas y seguridad; identifica contratos incompatibles, cobertura faltante y hallazgos pendientes. Para cada hallazgo, indica responsable, cambio requerido y cómo verificarlo; fundamenta el veredicto con evidencia, señala las pruebas pendientes y conserva las aprobaciones humanas, pues tu informe no las sustituye.",
              backstory="Eres el revisor final del equipo y reúnes una perspectiva transversal de arquitectura, datos y persistencia, backend, frontend, pruebas y seguridad. No das por válida una entrega solo porque cada etapa haya producido un informe: verificas que sus contratos y evidencias sean coherentes con los criterios de aceptación, señalas riesgos y correcciones concretas, y justificas el veredicto con lo que realmente está documentado. Respetas los checkpoints y las aprobaciones humanas: tu informe facilita la decisión del equipo, pero no la reemplaza.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un informe con VEREDICTO: APROBADO o RECHAZADO.', agent=agent)
