import logging
import os
import sys
from typing import Any, Dict
from dotenv import load_dotenv

from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from schemas import ExtraccionTecnica

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineTecnico")


class IncompleteGenerationError(Exception):
    """Excepción lanzada cuando el modelo interrumpe la respuesta por tokens insuficientes."""
    pass


def _verificar_finish_reason_y_extraer(resultado: Dict[str, Any]) -> ExtraccionTecnica:
    """
    Inspecciona la respuesta sin procesar para validar finish_reason y extraer el objeto parseado.
    Evita el error común de ignorar finish_reason='length' cuando el JSON queda truncado.
    """
    raw_message = resultado.get("raw")
    finish_reason = None

    if raw_message and hasattr(raw_message, "response_metadata"):
        finish_reason = raw_message.response_metadata.get("finish_reason")

    logger.info(f"Metadatos de respuesta del modelo - finish_reason: '{finish_reason}'")

    if finish_reason == "length":
        logger.error("Generación truncada por límite de tokens (finish_reason='length'). Lanzando reintento.")
        raise IncompleteGenerationError(
            "La respuesta del LLM fue cortada por límite de tokens antes de completar el JSON."
        )

    parsing_error = resultado.get("parsing_error")
    if parsing_error:
        logger.warning(f"Error de parsing detectado en la salida: {parsing_error}")
        raise OutputParserException(f"Error de parsing en salida estructurada: {parsing_error}")

    parsed = resultado.get("parsed")
    if parsed is None or not isinstance(parsed, ExtraccionTecnica):
        logger.warning("No se obtuvo una instancia válida de ExtraccionTecnica.")
        raise ValueError("El resultado estructurado es nulo o no coincide con ExtraccionTecnica.")

    logger.info("Validación Pydantic exitosa del objeto extraído.")
    return parsed


def get_llm(temperature: float = 0.0, api_key: str | None = None) -> ChatOpenAI:
    """
    Instancia el cliente de ChatOpenAI configurado con OpenRouter o endpoint compatible.
    Si la API key no está presente al importar, utiliza un valor temporal para no bloquear
    la inicialización de módulos y pruebas de esquemas.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        logger.warning(
            "OPENAI_API_KEY no encontrada en el entorno. "
            "Se requiere configurar OPENAI_API_KEY en .env para invocar llamadas reales al modelo."
        )
        key = "sk-placeholder-init-key"

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENAI_MODEL", "nvidia/nemotron-3.5-lightning:free")
    logger.info(f"Inicializando cliente ChatOpenAI en {base_url} con modelo: {model_name}")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "https://localhost",
            "X-Title": "PipelineTecnico"
        }
    )


def build_prompt_template() -> ChatPromptTemplate:
    """
    Crea el ChatPromptTemplate modular sin hardcodear F-strings.
    Permite que LangChain gestione las variables de entrada ({texto_entrada}).
    """
    system_instruction = (
        "Eres un arquitecto de software y analista de confiabilidad (SRE) experto en extracción "
        "de entidades técnicas y diagnóstico de sistemas.\n"
        "Tu misión es analizar el texto técnico provisto (descripciones de arquitectura, logs de error, "
        "o reportes de incidentes) y estructurar la información con rigurosidad.\n\n"
        "Directrices:\n"
        "1. Identifica todas las tecnologías, frameworks, bases de datos, lenguajes o herramientas mencionadas.\n"
        "2. Evalúa el nivel_de_criticidad (baja, media, alta) basado en la severidad del fallo o impacto sistémico.\n"
        "3. Sintetiza un resumen_tecnico descriptivo y profesional que refleje la situación o diseño descrito.\n"
        "4. Devuelve exclusivamente la información requerida cumpliendo con el esquema solicitado sin truncar la respuesta."
    )

    return ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "Analiza el siguiente texto y extrae las entidades técnicas correspondientes:\n\n{texto_entrada}")
    ])


def build_chain(model: ChatOpenAI | None = None):
    """
    Construye la cadena LCEL completa:
    Prompt + LLM con Structured Output + Validador de Finish Reason + Estrategia de Reintento (.with_retry())
    """
    if model is None:
        model = get_llm()

    prompt = build_prompt_template()

    # include_raw=True permite auditar finish_reason y atrapar parsing errors antes del contrato
    structured_model = model.with_structured_output(ExtraccionTecnica, include_raw=True)

    # Cadena LCEL base
    base_chain = (
        prompt
        | structured_model
        | RunnableLambda(_verificar_finish_reason_y_extraer)
    )

    # Añadir lógica de resiliencia con .with_retry()
    resilient_chain = base_chain.with_retry(
        retry_if_exception_type=(IncompleteGenerationError, OutputParserException, ValueError, Exception),
        stop_after_attempt=3,
        wait_exponential_jitter=True
    )

    return resilient_chain


# Instancia por defecto de la cadena
chain = build_chain()


async def process_text(text: str) -> ExtraccionTecnica:
    """
    Función asíncrona requerida que ejecuta el pipeline mediante .ainvoke().
    Incluye logs adecuados para observar el proceso de validación y posibles fallos.
    """
    logger.info("Iniciando procesamiento asíncrono de texto...")
    logger.debug(f"Longitud de entrada: {len(text)} caracteres.")

    try:
        resultado: ExtraccionTecnica = await chain.ainvoke({"texto_entrada": text})
        logger.info(
            f"Procesamiento finalizado con éxito. Criticidad: {resultado.nivel_de_criticidad.value} | "
            f"Tecnologías detectadas ({len(resultado.tecnologias)}): {resultado.tecnologias}"
        )
        return resultado
    except Exception as e:
        logger.error(f"Error irrecuperable durante el procesamiento del pipeline: {e}", exc_info=True)
        raise
