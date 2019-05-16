DROP TABLE IF EXISTS readings;

CREATE TABLE readings
(
    id UUID PRIMARY KEY, -- Primary Key column
    datetime TIMESTAMP,
    year INT,
    month INT,
    day INT,
    hour INT,
    minute INT,
    second INT,
    sunlight_mins FLOAT,
    temp FLOAT,
    rh FLOAT,
    dewp FLOAT,
    sensor_id INT
);

\i users.sql
GRANT ALL PRIVILEGES ON TABLE "readings" TO lambda_user;