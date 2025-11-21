# Multi-stage Dockerfile for Next.js (pnpm)
# Builder: install deps and build the app
FROM node:20-alpine AS builder
WORKDIR /app

# Install build tools for native modules (if needed)
RUN apk add --no-cache build-base python3 git

# Enable Corepack and activate pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package manifests first to leverage Docker cache
COPY package.json pnpm-lock.yaml* ./

# Install dependencies (uses lockfile)
RUN pnpm install

# Copy source and build
COPY . .
RUN pnpm build

# Runner: smaller image with only runtime artifacts
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Activate pnpm in runtime (so `pnpm start` works)
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy necessary files from builder
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

# Default command assumes `start` script runs `next start -p 3000`
CMD ["pnpm", "start"]
