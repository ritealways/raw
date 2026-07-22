# Why containerize at all: "works on my laptop" is the #1 cause of
# train/serve skew. Pinning the OS + Python + library versions here means
# the exact code that produced your offline MAPE is what runs in prod.
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
WORKDIR /app/src

# Default: run the full pipeline. Airflow/K8s override this CMD per task
# (e.g. `python pipeline.py` for training, `python forecast.py` for
# batch inference) so one image serves every stage -- no version drift
# between the container that trained the model and the one that serves it.
CMD ["python", "pipeline.py"]
