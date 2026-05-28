FROM node:24-bookworm-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

RUN corepack enable

COPY pnpm-workspace.yaml pnpm-lock.yaml ./
COPY frontend/package.json ./frontend/package.json
COPY packages/sdk-typescript/package.json ./packages/sdk-typescript/package.json
RUN pnpm install --filter @afrolete/frontend --frozen-lockfile

COPY frontend ./frontend

ARG NEXT_PUBLIC_AFROLETE_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_AFROLETE_AUTH_MODE=local
ENV NEXT_PUBLIC_AFROLETE_API_URL=${NEXT_PUBLIC_AFROLETE_API_URL} \
    NEXT_PUBLIC_AFROLETE_AUTH_MODE=${NEXT_PUBLIC_AFROLETE_AUTH_MODE}

WORKDIR /app/frontend

RUN pnpm run build

EXPOSE 3000
CMD ["pnpm", "exec", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
