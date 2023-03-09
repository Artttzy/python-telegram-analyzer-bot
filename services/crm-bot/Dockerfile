FROM python:3 as run
WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . .

EXPOSE 5284
ENTRYPOINT [ "python", "index.py" ]
