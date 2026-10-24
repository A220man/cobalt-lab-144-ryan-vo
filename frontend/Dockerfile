FROM node:24-alpine

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

USER appuser

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
