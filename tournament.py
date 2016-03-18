#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
from psycopg2 import DatabaseError


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def execute(query, values=()):
    """Execute a query in the database
    Args:
        query: query to execute
        values: tuple with query values used to avoid sql injection

    Raises DatabaseError if query couldn't be executed
    """
    db_conn = connect()
    cursor = db_conn.cursor()
    try:
        cursor.execute(query, values)
        db_conn.commit()
    except DatabaseError:
        pass
    db_conn.close()


def fetch_one(query):
    """Fetch one row from a table according to a query
    Args:
        query: query to execute

    Returns first value from the result tuple.
    """
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    db_conn.close()
    return result[0]


def fetch_all(query, values=()):
    """Fetch all rows from a table according to a query
    Args:
        query: query to execute
        values: tuple with query values used to avoid sql injection

    Returns a list of tuples with the results.
    """
    db_conn = connect()
    cursor = db_conn.cursor()
    cursor.execute(query, values)
    results = cursor.fetchall()
    db_conn.close()
    return results


def delete_matches():
    """Remove all the match records from the database."""
    query = "DELETE FROM {table_name}".format(table_name='matches')
    execute(query)


def delete_players():
    """Remove all the player records from the database."""
    query = "DELETE FROM {table_name}".format(table_name='players')
    execute(query)


def count_players():
    """Returns the number of players currently registered."""
    query = "SELECT COUNT(id) FROM {table_name}".format(table_name='players')
    return fetch_one(query)


def register_player(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    query = "INSERT INTO {table_name}(name) VALUES (%s)".format(table_name='players')
    execute(query, (name,))


def player_standings():
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
        SELECT v1.id, v1.name, v1.wins, v2.matches
        FROM view_player_id_name_won_matches as v1, view_player_matches as v2
        WHERE v1.id = v2.id
        ORDER BY v1.wins desc
    '''
    return fetch_all(query)


def report_match(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    query = "INSERT INTO {table_name}(winner, loser) VALUES (%s, %s)".format(table_name='matches')
    execute(query, (winner, loser))


def swiss_pairings():
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

    standings = player_standings()
    possible_matches = _get_possible_matches_for_next_round(standings)
    names, wins = _get_names_and_wins(standings)
    graph = _build_graph(possible_matches, wins)

    minimum_spanning_tree = _get_next_matches_ids(graph)

    next_matches = []
    for mst in minimum_spanning_tree:
        next_matches.append((mst[1], names[mst[1]], mst[2], names[mst[2]]))
    return next_matches


def _get_possible_matches_for_next_round(standings):
    possible_matches = {}

    for (id_player, name, win, matches) in standings:
        query = """SELECT p.id
            FROM players p WHERE p.id NOT IN (
                SELECT m.winner
                FROM matches m
                WHERE  m.loser = %s
            ) AND p.id NOT IN (
                SELECT m.loser
                FROM matches m
                WHERE  m.winner = %s
            ) AND p.id != %s
            """
        results = fetch_all(query, (id_player, id_player, id_player))
        possible_matches[id_player] = [res[0] for res in results]

    return possible_matches


def _get_names_and_wins(standings):
    wins = {}
    names = {}
    for (i, n, w, m) in standings:
        wins[i] = w
        names[i] = n

    return names, wins


def _build_graph(possible_matches, wins):
    graph = []
    for id_player1 in possible_matches:
        for id_player2 in possible_matches[id_player1]:
            graph.append((abs(wins[id_player1] - wins[id_player2]), id_player1, id_player2))

    graph.sort()
    return graph


def _get_next_matches_ids(graph):
    count_p = count_players()
    count, minimum_spanning_tree = find_shortest_path(graph, graph[0], count_p, [], set())
    i = 0
    while len(minimum_spanning_tree) != (count_p / 2):
        i += 1
        count, minimum_spanning_tree = find_shortest_path(graph, graph[i], count_p, [], set())

    # print 'Weight' + str(count)
    return minimum_spanning_tree


def find_shortest_path(graph, start, nr_players, nodes, path=set(), count=0):
    weight, id_player1, id_player2 = start
    nodes.append(id_player1)
    nodes.append(id_player2)
    path.add(start)
    count += weight

    if len(nodes) == nr_players:
        return count, path
    shortest = set()
    for edge in graph:
        weight1, id_player1, id_player2 = edge
        if id_player1 not in nodes and id_player2 not in nodes:
            new_count, new_path = find_shortest_path(graph, edge, nr_players, nodes, path, count)
            if new_path:
                if len(shortest) == 0 or new_count < count:
                    shortest = new_path
                    count = new_count

    return count, shortest
