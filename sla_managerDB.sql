USE sla_managerDB;
-- Comando SQL per creare la tabella SLA
CREATE TABLE sla (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    is_selected BOOLEAN DEFAULT FALSE
);

-- Comando SQL per creare la tabella VIOLATION
CREATE TABLE violation (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    sla_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actual_value FLOAT NOT NULL,
    is_violated BOOLEAN NOT NULL,
    FOREIGN KEY (sla_id) REFERENCES sla(id)
);
