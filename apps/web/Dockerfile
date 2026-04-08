FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
COPY tsconfig.base.json /app/tsconfig.base.json
COPY packages /app/packages
COPY apps/web /app/apps/web

WORKDIR /app/apps/web
RUN npm install

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
