# Edge image: build the React SPA, then serve it (static) + proxy /api.
# Build context = repo root (needs frontend/ and nginx/templates/).
FROM node:22-alpine AS build

# Baked into the bundle at build time (compose passes it from the root .env).
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/templates/default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
