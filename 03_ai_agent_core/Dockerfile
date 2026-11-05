FROM python:3.11-slim
WORKDIR /app

# Install CPU-only PyTorch from the official index
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

# Install the rest of the requirements (which no longer includes torch)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
