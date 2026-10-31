import pytest
from pydantic import ValidationError
from schemas import ExtraccionTecnica, NivelCriticidad
from chain import _verificar_finish_reason_y_extraer, IncompleteGenerationError
from langchain_core.messages import AIMessage


def test_schema_valido():
    """Valida la creación correcta de una entidad con datos bien formados."""
    datos = {
        "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
        "nivel_de_criticidad": "alta",
        "resumen_tecnico": "API con caché en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
    }
    objeto = ExtraccionTecnica(**datos)
    assert objeto.nivel_de_criticidad == NivelCriticidad.ALTA
    assert len(objeto.tecnologias) == 3
    assert "FastAPI" in objeto.tecnologias


def test_schema_tecnologias_vacias_falla():
    """Valida que falle si la lista de tecnologías está vacía."""
    with pytest.raises(ValidationError):
        ExtraccionTecnica(
            tecnologias=[],
            nivel_de_criticidad="media",
            resumen_tecnico="Descripción técnica válida de más de diez caracteres."
        )


def test_schema_tecnologias_blancas_falla():
    """Valida que falle si la lista solo contiene cadenas en blanco."""
    with pytest.raises(ValidationError):
        ExtraccionTecnica(
            tecnologias=["   ", ""],
            nivel_de_criticidad="baja",
            resumen_tecnico="Descripción técnica válida de más de diez caracteres."
        )


def test_schema_resumen_corto_falla():
    """Valida que falle si el resumen técnico es demasiado corto (< 10 caracteres)."""
    with pytest.raises(ValidationError):
        ExtraccionTecnica(
            tecnologias=["Python"],
            nivel_de_criticidad="baja",
            resumen_tecnico="Corto"
        )


def test_schema_criticidad_invalida_falla():
    """Valida que falle ante un valor de criticidad no contemplado en el Enum."""
    with pytest.raises(ValidationError):
        ExtraccionTecnica(
            tecnologias=["Python"],
            nivel_de_criticidad="urgente_invalido",
            resumen_tecnico="Descripción técnica válida de más de diez caracteres."
        )


def test_finish_reason_length_dispara_reintento():
    """Verifica que si el LLM devuelve finish_reason='length' se lance IncompleteGenerationError."""
    mensaje_crudo = AIMessage(
        content='{"tecnologias": ["Python"], "resumen',
        response_metadata={"finish_reason": "length"}
    )
    resultado = {
        "raw": mensaje_crudo,
        "parsed": None,
        "parsing_error": "JSONDecodeError"
    }
    with pytest.raises(IncompleteGenerationError):
        _verificar_finish_reason_y_extraer(resultado)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
