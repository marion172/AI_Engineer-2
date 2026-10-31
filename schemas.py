from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator


class NivelCriticidad(str, Enum):
    """Nivel de criticidad técnica o impacto del evento/arquitectura."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class ExtraccionTecnica(BaseModel):
    """
    Esquema estructurado para la extracción de entidades técnicas,
    evaluación de criticidad y síntesis contextual.
    """
    tecnologias: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de tecnologías, lenguajes, frameworks, bases de datos o herramientas identificadas en el texto."
    )
    nivel_de_criticidad: NivelCriticidad = Field(
        ...,
        description="Nivel de criticidad estimado (baja, media, alta) según el impacto del incidente o la severidad del componente analizado."
    )
    resumen_tecnico: str = Field(
        ...,
        min_length=10,
        description="Resumen conciso y técnico de la información extraída y del contexto evaluado."
    )

    @field_validator("tecnologias")
    @classmethod
    def validar_y_limpiar_tecnologias(cls, v: List[str]) -> List[str]:
        # Normalizar y remover valores vacíos o espacios
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("La lista de tecnologías no puede estar vacía ni contener solo cadenas en blanco.")
        # Eliminar duplicados preservando el orden
        seen = set()
        deduped = []
        for item in cleaned:
            if item.lower() not in seen:
                seen.add(item.lower())
                deduped.append(item)
        return deduped

    @field_validator("resumen_tecnico")
    @classmethod
    def validar_resumen(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 10:
            raise ValueError("El resumen técnico debe contener al menos 10 caracteres significativos.")
        return trimmed
