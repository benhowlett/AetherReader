# Stage 1: Build packages/shared
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
COPY tsconfig.base.json ./
COPY packages/shared ./packages/shared
COPY apps/web ./apps/web
COPY apps/api ./apps/api

# Install dependencies using workspaces
RUN npm ci

# Build shared package
WORKDIR /app/packages/shared
RUN npm run build

# Build web application
WORKDIR /app/apps/web
RUN npm run build

# Build api application
WORKDIR /app/apps/api
RUN npm run build

# Stage 2: Runtime
FROM node:20-slim
WORKDIR /app

# Install production dependencies only
COPY package*.json ./
COPY packages/shared/package*.json ./packages/shared/
COPY apps/api/package*.json ./apps/api/
RUN npm ci --omit=dev --workspace=@aetherreader/api --workspace=@aetherreader/shared

# Copy built artifacts
COPY --from=builder /app/packages/shared/dist ./packages/shared/dist
COPY --from=builder /app/apps/api/dist ./apps/api/dist
COPY --from=builder /app/apps/web/dist ./apps/web/dist

# Environment variables
ENV PORT=3001
ENV NODE_ENV=production
ENV DB_PATH=/data/sqlite.db

# Ensure data directory exists for persistence
RUN mkdir -p /data

EXPOSE 3001

# Start the API (which will serve the static web files)
WORKDIR /app/apps/api
CMD ["node", "dist/index.js"]
