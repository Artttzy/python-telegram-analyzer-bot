FROM node:lts AS install
WORKDIR /app
ARG SVC_ROOT=services/analyzer-core/sub-unsub-database
COPY ${SVC_ROOT}/package.json .
COPY ${SVC_ROOT}/tsconfig.json .
COPY ${SVC_ROOT}/yarn.lock .
COPY ${SVC_ROOT}/.env .

RUN yarn install --frozen-lockfile
COPY protos/* protos/
COPY ${SVC_ROOT}/scripts/* scripts/

RUN sh ./scripts/build-protos.sh "./protos"
COPY ${SVC_ROOT}/prisma/* prisma/
RUN npx prisma generate
COPY ${SVC_ROOT} .

FROM install as RUN
WORKDIR /app
EXPOSE 50001
ENTRYPOINT npx ts-node ./src/main.ts
