# Usamos una imagen de Go moderna
FROM golang:1.24-alpine

# 1. Instalar las herramientas de compilación de C necesarias para CGO en Alpine
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# 2. Habilitamos CGO explícitamente y luego compilamos el programa
RUN CGO_ENABLED=1 go build -o /nuevo-puente .

# El comando final para ejecutar nuestro puente
CMD [ "/nuevo-puente" ]