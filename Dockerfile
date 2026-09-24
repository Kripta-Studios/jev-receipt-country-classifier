FROM python:3.12-slim
WORKDIR /app
COPY jev_tickets ./jev_tickets
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
USER 10001
EXPOSE 8000
CMD ["python", "-m", "jev_tickets.web", "--host", "0.0.0.0"]
