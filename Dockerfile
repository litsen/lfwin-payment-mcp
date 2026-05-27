FROM node:20-slim

WORKDIR /app
COPY LICENSE ./LICENSE
COPY README.md ./README.md

COPY node-mcp/package*.json ./node-mcp/
WORKDIR /app/node-mcp
RUN npm ci --ignore-scripts

WORKDIR /app
COPY node-mcp/tsconfig.json ./node-mcp/tsconfig.json
COPY node-mcp/src ./node-mcp/src

WORKDIR /app/node-mcp
COPY LICENSE ./LICENSE
COPY README.md ./README.md
RUN npm run build && npm prune --omit=dev --ignore-scripts

CMD ["node", "dist/index.js"]
