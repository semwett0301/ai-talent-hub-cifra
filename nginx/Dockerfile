# Edge image: build the React SPA, then serve it (static) + proxy /api and /logs.
# Build context = repo root (needs frontend/ and nginx/templates/).
FROM node:22-alpine AS build

# Baked into the bundle at build time (compose passes them from the root .env).
# Deliberately without defaults: a missing value fails the build instead of shipping
# a bundle that calls the wrong path.
ARG SOURCES_API_PREFIX
ARG NEWS_API_PREFIX
ARG NPA_API_PREFIX
ENV SOURCES_API_PREFIX=$SOURCES_API_PREFIX \
    NEWS_API_PREFIX=$NEWS_API_PREFIX \
    NPA_API_PREFIX=$NPA_API_PREFIX

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/templates/default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
