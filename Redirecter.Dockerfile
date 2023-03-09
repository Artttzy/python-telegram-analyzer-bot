FROM node:lts AS INSTALL
WORKDIR /app
ARG SVC_ROOT=services/analyzer-core/redirect-service
ARG PRISMA_ROOT=services/analyzer-core/sub-unsub-database

COPY ${SVC_ROOT}/package.json .
COPY ${SVC_ROOT}/tsconfig.json .
COPY ${SVC_ROOT}/yarn.lock .

RUN yarn install --frozen-lockfile

COPY ${SVC_ROOT}/.env .
COPY ${PRISMA_ROOT}/prisma/* prisma/
RUN npx prisma generate

COPY ${SVC_ROOT} .

FROM INSTALL as RUN
WORKDIR /app
EXPOSE 30001
ENTRYPOINT npx ts-node ./src/main.ts