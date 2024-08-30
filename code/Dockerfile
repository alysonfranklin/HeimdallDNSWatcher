# Usar uma imagem base oficial do Python
FROM python:3.9-alpine

# Diretório de trabalho no contêiner
WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código para o contêiner
COPY app.py .

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
