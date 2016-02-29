-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP VIEW IF EXISTS view_player_id_name_won_matches CASCADE;
DROP VIEW IF EXISTS view_player_matches CASCADE;

-- CREATE players TABLE
CREATE TABLE players(id SERIAL PRIMARY KEY, name TEXT);

-- CREATE matches TABLE
CREATE TABLE matches(
    winner INTEGER REFERENCES players(ID),
    loser INTEGER REFERENCES players(ID)
);

-- CREATE view_player_id_name_won_matches VIEW
CREATE VIEW view_player_id_name_won_matches AS
    SELECT p.id, p.name, count(m.winner) as wins
    FROM players as p LEFT JOIN matches m
    ON p.id = m.winner
    GROUP BY p.id
    ORDER BY wins DESC;

-- CREATE view_player_matches VIEW
CREATE VIEW view_player_matches AS
    SELECT p.id, count(m.winner + m.loser) as matches
    FROM players as p LEFT JOIN matches m
    ON p.id = m.winner OR p.id = m.loser
    GROUP BY p.id;





