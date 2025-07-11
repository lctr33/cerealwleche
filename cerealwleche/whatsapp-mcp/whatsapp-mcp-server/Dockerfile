# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar solo el archivo de requisitos primero
COPY requirements.txt .

# Instalar TODAS las dependencias de la lista
RUN pip install --no-cache-dir -r requirements.txt

# Ahora, copiar el resto del código de la aplicación
COPY . .

# --- LÍNEA CORREGIDA Y DEFINITIVA ---
# Ejecuta el script directamente, ya que él mismo inicia el servidor.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
