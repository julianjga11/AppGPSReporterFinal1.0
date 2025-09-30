# Imagen base con Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer puerto 8080 (obligatorio en Cloud Run)
EXPOSE 8080

# Comando de inicio: usa la variable PORT (Cloud Run asigna 8080)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

