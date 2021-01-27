FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
COPY ./app /app
RUN pip install -r requirements.txt
WORKDIR /
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
