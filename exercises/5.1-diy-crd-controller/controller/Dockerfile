FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY controller.py .
RUN cat controller.py | head -5  # Verify copy

# Test CMD works
#CMD ["sh", "-c", "echo '=== STARTING ===' && python controller.py"]
CMD ["python", "controller.py"]
