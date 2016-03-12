#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
from psycopg2 import DatabaseError


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    query = "DELETE FROM {table_name}".format(table_name='matches')
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    db_conn.commit()


def deletePlayers():
    """Remove all the player records from the database."""
    query = "DELETE FROM {table_name}".format(table_name='players')
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    db_conn.commit()


def countPlayers():
    """Returns the number of players currently registered."""
    query = "SELECT COUNT(id) FROM {table_name}".format(table_name='players')
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0]


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    query = "INSERT INTO {table_name}(name) VALUES (%s)".format(table_name='players')
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query, (name,))
    db_conn.commit()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    query = '''
        SELECT p.id, p.name, p.wins, m.matches
        FROM view_player_id_name_won_matches as p, view_player_matches as m
        WHERE p.id = m.id
        ORDER BY p.wins desc
    '''
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    query = "INSERT INTO {table_name}(winner, loser) VALUES (%s, %s)".format(table_name='matches')
    db_conn = connect()
    cursor = db_conn.cursor()
    try:
        cursor.execute(query, (winner, loser))
        db_conn.commit()
    except DatabaseError as err:
        pass




def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    query = '''
        SELECT id, name
        FROM
        (SELECT id, name, row_number() OVER (ORDER BY wins DESC) as rnum
        FROM view_player_id_name_won_matches) q

        WHERE rnum %2 = 1

    '''
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    odd_row_results = cursor.fetchall()

    query = '''
        SELECT id, name
        FROM
        (SELECT id, name, row_number() OVER (ORDER BY wins DESC) as rnum
        FROM view_player_id_name_won_matches) q

        WHERE rnum %2 = 0

    '''
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    even_row_results = cursor.fetchall()

    results = []
    i = 0
    while i < len(odd_row_results):
        results.append(odd_row_results[i] + even_row_results[i])
        i += 1

    return results
