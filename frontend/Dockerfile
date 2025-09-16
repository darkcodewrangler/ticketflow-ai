# frontend/Dockerfile
FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY pnpm*.yaml ./
COPY package*.json ./
RUN npm install -g pnpm
RUN pnpm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Run in development mode (or build for production)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]