# FireTwin-Lite API image
FROM python:3.12.8-slim

WORKDIR /app

# Install dependencies first (cached layer when only the code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project and install the firetwin package
COPY pyproject.toml README.md ./
COPY ontology ./ontology
COPY queries ./queries
COPY shapes ./shapes
COPY src ./src
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000
CMD ["uvicorn", "firetwin.api:app", "--host", "0.0.0.0", "--port", "8000"]
