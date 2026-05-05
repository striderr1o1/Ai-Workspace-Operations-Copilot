FROM python:3.11-slim

WORKDIR /app 

COPY ./ ./

RUN pip install -r requirements.txt

RUN cd src/

CMD ["uvicorn", "main:app", "--reload", "--port", "3000"]
