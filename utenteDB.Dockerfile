FROM mysql:latest
 
ENV MYSQL_ROOT_PASSWORD=toor
ENV MYSQL_DATABASE=utenteDB
 
EXPOSE 6033
 
COPY ./utenteDB.sql /docker-entrypoint-initdb.d/
 