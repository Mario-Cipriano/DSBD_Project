FROM mysql:latest
 
ENV MYSQL_ROOT_PASSWORD=toor
ENV MYSQL_DATABASE=sla_managerDB
 
EXPOSE 6035
 
COPY ./sla_managerDB.sql /docker-entrypoint-initdb.d/