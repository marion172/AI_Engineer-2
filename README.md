# Pipeline de Procesamiento Validado
## AI Engineer - Extracción de Entidades Técnicas con LCEL y Pydantic

Este proyecto implementa un Pipeline de Extracción de Entidades Técnicas resiliente y validado utilizando el stack moderno de LangChain (LCEL) y Pydantic v2. 

> [!NOTE]
> **Configuración del Proveedor LLM:**
> Para permitir la ejecución y evaluación del proyecto sin costo de tokens ni requerir una tarjeta de crédito, el cliente estándar `ChatOpenAI` se configuró apuntando al gateway compatible de OpenRouter (`https://openrouter.ai/api/v1`) utilizando el modelo gratuito `nvidia/nemotron-3.5-lightning:free`. Genera una cuenta en openrouter obtienes tu key y lo agregas al proyecto
>
> - Utiliza la sintaxis de composición pura de LCEL y resiliencia con `.with_retry()`.
> - Es intercambiable sin cambiar el código: si se desea usar la API directa de OpenAI (`gpt-4o-mini`), únicamente se actualizan las credenciales en el `.env`.

---

##  Componentes del Sistema

1. **Esquema Pydantic [schemas.py]**:
   - `tecnologias`: Lista de strings con validación de no vaciedad, limpieza de espacios y desduplicación.
   - `nivel_de_criticidad`: `Enum` tipado con valores permitidos (`baja`, `media`, `alta`).
   - `resumen_tecnico`: String descriptivo con longitud mínima garantizada de 10 caracteres significativos.

2. **Template Modular [chain.py]**:
   - Implementado con `ChatPromptTemplate` permitiendo a LangChain administrar las variables de entrada (`{texto_entrada}`) y el rol de sistema de forma desacoplada.

3. **Cadena LCEL con Salida Estructurada**:
   - Composición:
     ```python
     chain = (
         prompt 
         | model.with_structured_output(ExtraccionTecnica, include_raw=True)
         | RunnableLambda(_verificar_finish_reason_y_extraer)
     ).with_retry(...)
     ```

4. **Lógica de Resiliencia y Detección de `finish_reason`**:
   - **Prevención de truncamiento**: Mediante `include_raw=True`, el pipeline audita los metadatos de respuesta (`response_metadata["finish_reason"]`). Si el modelo interrumpe la respuesta por límite de tokens (`finish_reason == "length"`), se levanta un `IncompleteGenerationError`.
   - **Reintentos automáticos**: Se utiliza `.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)` para reintentar la llamada en caso de respuestas incompletas, JSON malformado o errores transitorios de red.

5. **Ejecución Asíncrona y Observabilidad**:
   - Función asíncrona `async def process_text(text: str) -> ExtraccionTecnica` que ejecuta la cadena con `.ainvoke()`.
   - Registro de logs informativos y de depuración a través de `logging` en cada etapa del pipeline.

---

##  Estructura del Proyecto

```
AI_Engineer-2/
├── schemas.py          # Definición de modelos Pydantic y validadores
├── chain.py            # Cadena LCEL, ChatPromptTemplate, .with_retry() y process_text()
├── main.py             # Mini-script ejecutable con casos de prueba
├── test_schemas.py     # Suite de pruebas unitarias (Pytest)
├── requirements.txt    # Dependencias del proyecto
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Exclusiones de Git
└── README.md           # Documentación e instrucciones
```

---

##  Ejemplo de Entrada y Salida

### Entrada:
> *"Implementamos una arquitectura de microservicios distribuida construida en Go con comunicación inter-servicio mediante gRPC y Protocol Buffers. Para la exposición externa utilizamos Kong como API Gateway, mientras que la persistencia transaccional se gestiona en un clúster de MongoDB. Durante las pruebas de carga identificamos problemas de latencia elevada debido a la serialización y timeouts en el gateway."*

### Salida Validada (JSON):
```json
{
  "tecnologias": [
    "Go",
    "gRPC",
    "Protocol Buffers",
    "Kong",
    "MongoDB"
  ],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "La arquitectura corresponde a una distribución de microservicios implementada en Go, con comunicación inter-servicio mediante gRPC y Protocol Buffers. Se utiliza Kong como API Gateway para exposición externa y MongoDB como capa de persistencia transaccional. Durante pruebas de carga se identificaron problemas de latencia elevada y timeouts en el gateway, atribuidos a la capa de serialización, lo que requiere optimización de la cadena de comunicación y configuración del gateway para cumplir con los objetivos de rendimiento y disponibilidad."
}
```

---

## ⚙️ Requisitos Previos e Instalación

### 1. Clonar o acceder a la carpeta del proyecto
```bash
cd AI_Engineer-2
```

### 2. Crear y activar un entorno virtual

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**En Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno
Crea un archivo `.env` basado en `.env.example`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

Edita `.env` con tu clave de API (OpenRouter u OpenAI):
```ini
OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=nvidia/nemotron-3.5-lightning:free
```

---

## 🚀 Ejecución

### Ejecutar el script principal de demostración
Ejecuta los 3 casos de prueba integrales (arquitectura, logs de error e incidentes, y texto ambiguo):

```bash
python main.py
```

### Ejecutar las pruebas unitarias (Pytest)
Verifica las validaciones de Pydantic, restricciones de entrada y la detección de `finish_reason='length'`:

```bash
pytest -v
```

