-- Table and Views definitions for the tournament project.


-- CLEAN DATABASE: DROP VIEWS AND TABLES
DROP VIEW IF EXISTS view_player_id_name_won_matches;
DROP VIEW IF EXISTS view_player_matches;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;


-- CREATE players TABLE
CREATE TABLE players(id SERIAL PRIMARY KEY, name TEXT);

-- CREATE matches TABLE
CREATE TABLE matches(
    winner INTEGER REFERENCES players(ID),
    loser INTEGER REFERENCES players(ID)
);

-- TRIGGER PROCEDURE FOR PREVENTING REMATCHES
-- This procedure prevents adding matches that have already been played.
-- If we have a match between winner with id: 1, and loser with id: 3, this
-- procedure raises an exception if we try to add (1,3) or (3,1) in the matches table.
-- Also an exception is raised when we try to add a match where the winner and loser have
-- the same ids, ex: (1,1), (3,3) etc.

CREATE OR REPLACE FUNCTION prevent_rematches_trigger()
    RETURNS trigger AS
$BODY$
BEGIN
    if exists
    (select * from matches where
        (winner = NEW.winner and loser= NEW.loser) or
        (winner = NEW.loser and loser=NEW.winner)
    ) then
        raise EXCEPTION 'The match has already been played.';
        return null;
    end if;

    if exists (select * from matches where NEW.winner = NEW.loser) then
        raise EXCEPTION 'A player cant play against himself.';
        return null;
    end if;

    RETURN NEW;
END;
$BODY$
language plpgsql;

-- TRIGGER FOR PREVENTING REMATCHES
-- This trigger executes prevent_rematches_trigger on each row before insert.
CREATE TRIGGER prevent_rematches
  BEFORE INSERT
  ON matches
  FOR EACH ROW
  EXECUTE PROCEDURE prevent_rematches_trigger();

-- CREATE view_player_id_name_won_matches VIEW
-- This view returns a list of the players (id, name) and their win records, sorted by wins.
CREATE VIEW view_player_id_name_won_matches AS
    SELECT p.id, p.name, count(m.winner) as wins
    FROM players as p LEFT JOIN matches m
    ON p.id = m.winner
    GROUP BY p.id
    ORDER BY wins DESC;

-- CREATE view_player_matches VIEW
-- This view returns the nr of matches of each player.
CREATE VIEW view_player_matches AS
    SELECT p.id, count(m.winner + m.loser) as matches
    FROM players as p LEFT JOIN matches m
    ON p.id = m.winner OR p.id = m.loser
    GROUP BY p.id;



