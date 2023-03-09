FROM python:3 as RUNNER
WORKDIR /app
ARG CLIENT_ROOT=services/spam-bot

COPY ${CLIENT_ROOT}/requirements.txt .
RUN python -m pip install -r requirements.txt
COPY ${CLIENT_ROOT}/scripts/* scripts/
COPY protos/* protos/
RUN sh ./scripts/build-protos.sh ./protos
COPY ${CLIENT_ROOT}/* ./
ENTRYPOINT ["python", "index.py"]
