FROM cubejs/cube:latest

# Copy configuration and schema into the expected Cube.js conf directory
COPY cube.js /cube/conf/cube.js
COPY schema /cube/conf/schema
COPY package.json /cube/conf/package.json

WORKDIR /cube/conf

# Install DuckDB driver
RUN npm install

EXPOSE 4000
