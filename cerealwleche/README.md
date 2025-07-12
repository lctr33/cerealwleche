# Agente de Ventas para WhatsApp con IA

Este es un proyecto de un agente conversacional avanzado que opera a través de WhatsApp. Está diseñado para gestionar la venta de perfiles de servicios de streaming, utilizando un modelo de lenguaje grande (LLM) para entender y responder a los usuarios de forma natural, y manteniendo el contexto de la conversación para interacciones coherentes.

El sistema es proactivo: detecta nuevos mensajes automáticamente y puede manejar flujos de conversación complejos, incluyendo consultas de productos, procesos de compra y un ciclo de confirmación de pago con intervención humana (administrador).

## ✨ Funcionalidades Actuales

* **Agente Proactivo:** Un servicio dedicado monitorea constantemente la llegada de nuevos mensajes de WhatsApp.
* **Procesamiento de Lenguaje Natural:** Utiliza un LLM (configurable para Ollama, OpenAI o DeepSeek) para entender la intención del usuario.
* **Manejo de Múltiples Intenciones:** Puede identificar si un usuario está saludando, pidiendo una lista completa de servicios, preguntando por un producto específico, intentando comprar o confirmando un pago.
* **Memoria Conversacional:** Mantiene el historial de cada chat para dar respuestas contextuales y no repetir información.
* **Flujo de Venta Completo:**
    1.  Presenta un desglose de precios al usuario.
    2.  Guarda un "pedido en progreso" mientras espera la confirmación.
    3.  Notifica al administrador cuando un usuario avisa de un pago.
    4.  Espera la confirmación del administrador para liberar las credenciales al cliente.
* **Control por Chat:** Permite activar o desactivar las respuestas automáticas para conversaciones específicas a través de una herramienta de API.
* **Persistencia de Datos:** Utiliza bases de datos dedicadas para el historial de WhatsApp y los datos del negocio (cuentas y precios).

## 📋 Requerimientos

Para ejecutar este proyecto en una nueva máquina (probado en Ubuntu 24), necesitarás:

* **Docker:** Para gestionar los contenedores de los microservicios.
* **Docker Compose:** Para orquestar la red de contenedores.
* **Go:** Versión **1.24** o superior. Necesario para preparar las dependencias de nuestro puente de WhatsApp personalizado.
* **API Key:** Una clave de API para el proveedor de LLM que elijas (OpenAI o DeepSeek).
* **Número de Administrador:** Un número de WhatsApp para recibir las notificaciones de pago.

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para levantar el sistema en un entorno nuevo:

1.  **Copiar el Proyecto:**
    No clones el repositorio original. Copia esta carpeta de proyecto completa a la nueva máquina, ya que contiene todos los arreglos, archivos nuevos y mejoras que hemos implementado.

2.  **Instalar Docker y Docker Compose:**
    Se recomienda seguir la guía oficial de Docker para instalar `Docker Engine` y `Docker Compose Plugin`. Los comandos que usamos fueron:
    ```bash
    # Instalar prerrequisitos y la clave GPG de Docker
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL [https://download.docker.com/linux/ubuntu/gpg](https://download.docker.com/linux/ubuntu/gpg) | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Añadir el repositorio de Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] [https://download.docker.com/linux/ubuntu](https://download.docker.com/linux/ubuntu) $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

3.  **Instalar Go:**
    La forma más sencilla y recomendada en Ubuntu es a través de Snap para obtener la versión más reciente.
    ```bash
    sudo snap install go --classic
    ```

4.  **Preparar Dependencias del Puente de Go:**
    Este paso es crucial y se hace una sola vez por máquina.
    ```bash
    # Navega a la carpeta de nuestro puente personalizado
    cd ruta/a/tu/proyecto/cerealwleche/nuevo_puente_go
    
    # Este comando descarga las librerías necesarias para el puente
    go mod tidy
    ```

5.  **Configurar Variables de Entorno:**
    * Regresa a la carpeta raíz del proyecto.
    * Copia el archivo de ejemplo: `cp .env.example .env`.
    * Abre el archivo `.env` (`nano .env`) y configura las contraseñas de la base de datos.
    * Abre el archivo `docker-compose.yml` (`nano docker-compose.yml`) y, en la sección `environment` del servicio `host_app`, añade tus claves de API y tu número de administrador.
        ```yaml
        environment:
          # ...
          ADMIN_PHONE_NUMBER: "521NUMEROADMIN"
          OPENAI_API_KEY: "sk-..."
          DEEPSEEK_API_KEY: "sk-..."
        ```

6.  **Lanzar el Sistema:**
    Desde la carpeta raíz del proyecto, ejecuta:
    ```bash
    sudo docker compose up --build -d
    ```
    La opción `-d` lo deja corriendo en segundo plano.

7.  **Configuración Inicial (Única Vez):**
    * **Vincular WhatsApp:** Escanea el código QR que aparecerá en los logs del puente.
        ```bash
        sudo docker compose logs -f whatsapp_go_bridge
        ```
    * **Descargar Modelo de IA (si usas Ollama):**
        ```bash
        sudo docker exec -it ollama_ai ollama pull phi3:mini
        ```

¡Y listo! El agente estará completamente funcional y listo para recibir mensajes.
