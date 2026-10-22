"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'user_story.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Analiza el Issue, sus criterios de aceptación y las interfaces del producto.
Define componentes, responsabilidades y límites del cambio.
Especifica entradas, respuestas y errores de la API, con ejemplos.
Relaciona cada criterio con el componente que lo resuelve. Declara supuestos y preguntas pendientes.
Entrega user_story.md con componentes, contrato de API y criterios verificables."""
agent = Agent(role='Arquitecto de solución',
              goal="Traducir el Issue y sus criterios de aceptación en componentes, contrato de API y criterios verificables, declarando supuestos y preguntas pendientes.",
              backstory="Eres el arquitecto del equipo. Lees el Issue y las interfaces existentes antes de proponer nada, "
                        "delimitas el alcance del cambio y dejas explícito qué decisiones necesitan Datos, Backend y Frontend.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un user_story.md con componentes, contrato de API con ejemplos de entrada, respuesta y error, '
                                'criterios verificables y lista de supuestos y preguntas pendientes.', agent=agent)
