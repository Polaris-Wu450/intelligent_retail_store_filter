# Build React app → ../static/dist, then serve with nginx + /api → Django
FROM node:20-alpine AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/static/dist /usr/share/nginx/html
COPY frontend/nginx.docker.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
