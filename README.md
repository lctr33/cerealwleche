# Agente de IA para Venta de Cuentas de Streaming

Este proyecto implementa un agente de inteligencia artificial diseñado para automatizar la venta de perfiles de cuentas de streaming (Netflix, Spotify, etc.). El agente utiliza un Modelo de Lenguaje Grande (LLM) para interactuar, gestiona un inventario de cuentas a través de una base de datos, y está preparado para integraciones de pago y comunicación vía WhatsApp.

La arquitectura se basa en microservicios orquestados con Docker Compose y utiliza el Protocolo de Contexto del Modelo (MCP) para la comunicación entre el agente principal y sus herramientas.

## 🌟 Características Principales (Versión Actual)

* **Procesamiento de Lenguaje Natural**: Utiliza un LLM (vía Ollama con Llama 3) para entender las peticiones de los usuarios.
* **Gestión de Consultas**:
    * Puede listar los servicios de streaming disponibles.
    * Puede listar los planes y precios para un servicio específico.
    * Puede buscar perfiles disponibles para un servicio y duración específicos.
* **Simulación de Flujo de Venta**:
    * Genera un link de pago simulado cuando un cliente solicita una cuenta.
    * Tras una simulación de "pago exitoso" (vía un endpoint de webhook), el agente:
        * Registra/actualiza al cliente en la base de datos.
        * Marca el perfil como vendido.
        * Obtiene las credenciales de la cuenta.
        * Envía las credenciales al cliente a través de WhatsApp.
* **Arquitectura Modular con MCP**:
    * El agente principal (Anfitrión FastAPI) se comunica con herramientas expuestas por servidores MCP dedicados (uno para la base de datos y otro para WhatsApp).
* **Contenerizado con Docker**: Todos los servicios (agente, servidores MCP, base de datos, Ollama, puente de WhatsApp) están definidos y se ejecutan con Docker Compose para facilitar el desarrollo y despliegue.
* **Integración con WhatsApp**: Utiliza el proyecto [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) (modificado) para enviar mensajes.

## 🛠️ Prerrequisitos

* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/) (generalmente viene con Docker Desktop o se instala como plugin de Docker).
* [Git](https://git-scm.com/downloads) (para clonar este repositorio y el de WhatsApp si es necesario).
* Una cuenta personal de WhatsApp para conectar el puente (`lharries/whatsapp-mcp`).
* (Opcional) `uv` para gestionar entornos Python si se trabaja fuera de Docker: `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## ⚙️ Configuración

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/lctr33/cerealwleche
    cd cereal-with-leche
    ```

2.  **Componente de WhatsApp (`lharries/whatsapp-mcp`):**
    Este proyecto utiliza una versión modificada de [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) para la funcionalidad de WhatsApp.

3.  **Variables de Entorno:**
    El sistema se configura mediante variables de entorno. Crea un archivo llamado `.env` en la raíz del proyecto (`cereal-with-leche/`) copiando el archivo de ejemplo:
    ```bash
    cp .env.example .env
    ```
    Luego, **edita el archivo `.env`** con tus propios valores. El contenido del `.env.example` es:
    ```env
    # Archivo de ejemplo para variables de entorno

    # Configuración de la Base de Datos MySQL para Docker Compose
    MYSQL_HOST_PORT=3307 # Puerto en el que la DB será accesible desde tu máquina host
    MYSQL_ROOT_PASSWORD=tu_password_root_segura_aqui # Contraseña para el usuario root de MySQL
    MYSQL_DATABASE=streaming_profiles # Nombre de la base de datos a crear
    MYSQL_USER=cereal-with-leche      # Usuario de la aplicación para la base de datos
    MYSQL_PASSWORD=bryanesgei         # Contraseña para el usuario de la aplicación

    # URLs internas de Docker para la comunicación entre servicios (no suelen necesitar cambio)
    # OLLAMA_HOST=http://ollama_service:11434
    # DB_MCP_SERVER_URL=http://db_mcp_server:8001
    # WHATSAPP_MCP_SERVER_URL=http://whatsapp_python_mcp_server:8002/mcp/

    # Para cuando implementes MercadoPago real (actualmente no usado en el flujo principal)
    # MERCADOPAGO_ACCESS_TOKEN=TU_APP_USR_DE_MERCADOPAGO
    # BASE_URL_NGROK=https://tu_url_de_ngrok.ngrok-free.app # Para webhooks de MercadoPago

    # Para OpenAI (opcional, si cambias el proveedor de LLM en main.py)
    # OPENAI_API_KEY=sk-xxxxxxxxxxxx
    ```

4.  **Base de Datos Inicial:**
    El archivo `base_datos.sql` (que debes tener en la raíz del proyecto) se usará automáticamente para inicializar la estructura y los datos de la base de datos MySQL la primera vez que se levanten los contenedores Docker. 

## 🚀 Ejecución

1.  Asegúrate de que Docker Desktop o Docker Engine esté corriendo.
2.  Desde la raíz de tu proyecto (`cereal-with-leche/`), ejecuta:
    ```bash
    sudo docker compose up --build -d
    ```
    * `--build`: Reconstruye las imágenes si ha habido cambios en los `Dockerfile`s o el código fuente. Es bueno usarlo la primera vez o después de cambios.
    * `-d`: Corre los contenedores en modo "detached" (en segundo plano). Si quieres ver todos los logs en la terminal actual, omite `-d`.

3.  **Verificar Estado de los Contenedores:**
    ```bash
    sudo docker compose ps
    ```
    Todos los servicios deberían estar en estado `Up` o `running (healthy)`.

4.  **Primera Vez con el Puente de WhatsApp:**
    * El contenedor `whatsapp_go_bridge` necesitará autenticarse con tu WhatsApp escaneando un código QR. Revisa sus logs:
        ```bash
        sudo docker compose logs -f whatsapp_go_bridge
        ```
    * Escanea el QR que aparezca usando la opción "Dispositivos Vinculados" en tu WhatsApp móvil.
    * Una vez conectado, la sesión se guardará en el volumen Docker `whatsapp_store_volume` y no necesitarás escanear el QR de nuevo a menos que la sesión expire o elimines el volumen.
    * Puede tomar unos minutos para que cargue todos tus chats.

5.  **Primera Vez con Ollama:**
    * El servicio `ollama_service` necesita tener el modelo LLM descargado. Ejecuta en otra terminal:
        ```bash
        sudo docker exec -it ollama_ai ollama pull llama3:8b
        ```
    * Esto descargará el modelo `llama3:8b` y se guardará en el volumen `ollama_data_volume`. Solo necesitas hacerlo una vez.

## ⚙️ Descripción de los Servicios (Contenedores Docker)

* **`host_fastapi_app`**: El agente principal (Anfitrión FastAPI con LangChain). Accesible en `http://localhost:8000`. Documentación de la API en `http://localhost:8000/docs`.
* **`db_mcp_server`**: Servidor MCP escrito en Python que expone las herramientas para interactuar con la base de datos MySQL. Escucha en el puerto `8001` (interno a Docker, accesible para `host_fastapi_app` como `http://db_mcp_server:8001`).
* **`mysql_streaming_db`**: La base de datos MySQL. Accesible desde tu máquina host en el puerto especificado por `MYSQL_HOST_PORT` (por defecto 3307).
* **`whatsapp_go_bridge`**: El componente en Go del servidor `lharries/whatsapp-mcp` que se conecta directamente a WhatsApp Web. Expone una API REST interna en el puerto `8080`.
* **`whatsapp_python_mcp_server`**: El servidor MCP en Python del proyecto `lharries/whatsapp-mcp` que expone las herramientas de WhatsApp. Escucha en el puerto `8002` (interno a Docker, accesible para `host_fastapi_app` como `http://whatsapp_python_mcp_server:8002/mcp/`).
* **`ollama_service`**: El servicio Ollama para correr el LLM. Accesible desde `host_fastapi_app` como `http://ollama_service:11434` y desde tu máquina host en `http://localhost:11434`.

## 🧪 Cómo Probar

1.  **Accede a la Interfaz del Agente Anfitrión**: Abre tu navegador y ve a `http://localhost:8000/docs`.
2.  **Probar el Endpoint `/chat`**:
    * Usa el método `POST` para `/chat`.
    * Proporciona un cuerpo JSON como:
        ```json
        {
          "texto": "Dame una cuenta de crunchyroll de un mes",
          "telefono_cliente": "TU_NUMERO_DE_WHATSAPP_CON_CODIGO_PAIS_SIN_+", 
          "nombre_cliente": "Nombre de Prueba"
        }
        ```
    * Deberías recibir un mensaje en tu WhatsApp (en el número `TU_NUMERO_DE_WHATSAPP_CON_CODIGO_PAIS_SIN_+`) con el enlace de pago simulado.
3.  **Simular Webhook de Pago Exitoso**:
    * Después de la llamada a `/chat`, el agente habrá guardado el `id_perfil` asociado. Revisa los logs de `host_fastapi_app` para identificar este `id_perfil`.
    * Envía una petición `POST` a `http://localhost:8000/webhook/mercadopago` con un cuerpo como:
        ```json
        {
          "type": "payment",
          "data": { "id": "pago_simulado_123" },
          "external_reference": "ID_DEL_PERFIL_OBTENIDO_EN_EL_PASO_ANTERIOR",
          "status": "approved"
        }
        ```
        (Reemplaza `ID_DEL_PERFIL_OBTENIDO_EN_EL_PASO_ANTERIOR` por el `id_perfil` real).
    * Deberías recibir un mensaje de WhatsApp con las credenciales de la cuenta.
    * Revisa los logs de todos los contenedores para ver el flujo completo.

## 🙏 Atribución

* La funcionalidad de WhatsApp de este proyecto se basa en el excelente trabajo de [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp). Se han realizado modificaciones para su integración en esta arquitectura Docker y para el modo de transporte HTTP del servidor MCP de Python.

## 🚀 Próximos Pasos (Desarrollo Futuro)

* Integración real con la API de Mercado Pago para generar links de pago y procesar webhooks.
* Implementar la recepción de mensajes de WhatsApp en `main.py` (probablemente mediante sondeo/polling al servidor MCP de WhatsApp) para permitir una conversación bidireccional completa.
* Mejorar el manejo de errores y la robustez general.
* Añadir más herramientas y capacidades al agente.
