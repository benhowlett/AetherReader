# Stage 1: Build
FROM node:20-slim AS builder
WORKDIR /app

# Copy the whole project for context (needed for monorepo/workspaces)
COPY . .

# Install all dependencies (handles workspaces)
RUN npm ci

# Build shared package first
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

# Set production environment
ENV NODE_ENV=production
ENV PORT=3001
ENV DB_PATH=/data/sqlite.db

# Install ONLY production dependencies across the workspace
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/packages/shared/package*.json ./packages/shared/
COPY --from=builder /app/apps/api/package*.json ./apps/api/
COPY --from=builder /app/apps/web/package*.json ./apps/web/

RUN npm ci --omit=dev --workspace=@aetherreader/api --workspace=@aetherreader/shared

# Copy built artifacts and shared library
COPY --from=builder /app/packages/shared/dist ./packages/shared/dist
COPY --from=builder /app/apps/api/dist ./apps/api/dist
COPY --from=builder /app/apps/web/dist ./apps/web/dist

# Ensure data directory exists for persistence
RUN mkdir -p /data

EXPOSE 3001

# Start the API (which serves static web files in production)
WORKDIR /app/apps/api
CMD ["node", "dist/index.js"]
