FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY package.json /app/package.json
RUN npm install

COPY . /app

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]

