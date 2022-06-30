DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS savedSearches;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q1 INTEGER,
    q2 INTEGER,
    q3 INTEGER,
    q4 INTEGER,
    q5 INTEGER,
    comment TEXT
);

CREATE TABLE savedSearches
(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER,
	date           TEXT,
    loc_name       TEXT,
    lat_in         TEXT,
    long_in        TEXT,
    rotate_in      TEXT,
    surface_type   TEXT,
    year           TEXT
	irradiance_max INTEGER
);