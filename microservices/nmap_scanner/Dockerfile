FROM node:20-alpine

# Install nmap and required system dependencies
RUN apk add --no-cache \
    nmap \
    nmap-scripts \
    curl \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --omit=dev

# Copy source code
COPY src/ ./src/

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nmap -u 1001 -G nodejs

# Create directory for XML files
RUN mkdir -p /app/temp && chown -R nmap:nodejs /app

# Switch to non-root user
USER nmap

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8004/health || exit 1

# Start the application
CMD ["node", "src/main.js"]
