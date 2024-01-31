USE weatherDB;
CREATE TABLE subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    countrycode VARCHAR(10) NOT NULL,
    minTemp FLOAT NOT NULL,
    maxTemp FLOAT NOT NULL,
    rain FLOAT NOT NULL,
    snow TINYINT(1) NOT NULL
);
