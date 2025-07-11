# Usar una imagen base de Go
FROM golang:1.24-alpine

# Instalar las dependencias necesarias para construir
RUN apk add --no-cache build-base

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de dependencias y descargarlas
COPY go.mod go.sum ./
RUN go mod download

# Copiar todo el código fuente
COPY . .

# Construir la aplicación
RUN go build -o /whatsapp-bridge .

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD [ "/whatsapp-bridge" ]
