import asyncio
import json
import logging
from chain import process_text
from schemas import ExtraccionTecnica

CASOS_DE_PRUEBA = [
    {
        "nombre": "Caso 1: Arquitectura de Software (Microservicios)",
        "texto": (
            "Implementamos una arquitectura de microservicios distribuida construida en Go con "
            "comunicación inter-servicio mediante gRPC y Protocol Buffers. Para la exposición "
            "externa utilizamos Kong como API Gateway, mientras que la persistencia transaccional "
            "se gestiona en un clúster de MongoDB. Durante las pruebas de carga identificamos "
            "problemas de latencia elevada debido a la serialización y timeouts en el gateway."
        )
    },
    {
        "nombre": "Caso 2: Log de Error e Incidente Crítico",
        "texto": (
            "CRITICAL 2026-10-15 14:22:01 [Worker-3] kafka.errors.KafkaTimeoutError: "
            "Failed to send messages to topic 'orders-stream' after 60000 ms. "
            "Kubernetes pod 'checkout-service-7f98b-q2d8z' restarted with OOMKilled code 137. "
            "RabbitMQ dead-letter queue backup activated."
        )
    },
    {
        "nombre": "Caso 3: Prueba de Estrés / Texto Ambiguo",
        "texto": (
            "El script parece funcionar a veces cuando corro python test.py, pero Docker "
            "no levanta la imagen porque faltan dependencias en el Dockerfile. La app no es crítica "
            "pero es molesto."
        )
    }
]


async def ejecutar_pruebas():
    print("=" * 80)
    print("EJECUCIÓN DEL PIPELINE DE EXTRACCIÓN DE ENTIDADES TÉCNICAS")
    print("=" * 80)

    for idx, caso in enumerate(CASOS_DE_PRUEBA, 1):
        print(f"\n--- {caso['nombre']} ---")
        print(f"Texto de entrada:\n\"{caso['texto']}\"\n")

        try:
            resultado: ExtraccionTecnica = await process_text(caso["texto"])

            print(" Salida validada (Pydantic / JSON):")
            print(json.dumps(resultado.model_dump(), indent=2, ensure_ascii=False))
        except Exception as err:
            print(f" Falló el procesamiento para el caso: {err}")

    print("\n" + "=" * 80)
    print("FIN DE LA EJECUCIÓN")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(ejecutar_pruebas())
