-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


-- CREATE players TABLE
CREATE TABLE players(id SERIAL PRIMARY KEY, name TEXT);

-- CREATE matches TABLE
CREATE TABLE matches(
    winner INTEGER REFERENCES players(ID),
    loser INTEGER REFERENCES players(ID)
);

