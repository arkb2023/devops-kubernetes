FROM python:3.12-slim
WORKDIR /app
COPY cron_wiki_todo.py .
RUN pip install requests
CMD ["python", "cron_wiki_todo.py"]
