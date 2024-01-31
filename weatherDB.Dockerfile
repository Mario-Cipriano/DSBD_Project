FROM mysql:latest
 
ENV MYSQL_ROOT_PASSWORD=toor
ENV MYSQL_DATABASE=weatherDB
 
EXPOSE 6034
 
COPY ./weatherDB.sql /docker-entrypoint-initdb.d/