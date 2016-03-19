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

    shortest_path = _get_next_matches_ids(graph)

    next_matches = []
    for shp in shortest_path:
        next_matches.append((shp[1], names[shp[1]], shp[2], names[shp[2]]))
    return next_matches


def _get_possible_matches_for_next_round(standings):
    """Returns possible next matches for next round.

    Args:
        standings: actual standings for each player

    Returns:
        A dictionary with possible next matches for each player
        {id1: [id2, id3, ...], id2: [id1, id4, id5...], ...}

        idn: a player's unique id
    """
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
    """Returns 2 dictionaries: one with nr of wins and the other with names of the players.

    Args:
        standings: actual standings for each player

    Returns:
        2 lists:
        wins = {'id1': 2, 'id2': 1, ...}
        names = {'id1': 'Player 1', 'id2': 'Player 2', ...}

        idn: a player's unique id
    """
    wins = {}
    names = {}
    for (i, n, w, m) in standings:
        wins[i] = w
        names[i] = n

    return names, wins


def _build_graph(possible_matches, wins):
    """Returns a list with all combinations of possible next matches and their weight.

    Args:
        possible_matches
        wins: used to calculate weight of a match

    Returns:
        A list of tuples: [(weight1, id1, id2), (weight2, id1, id4), ...]

        weightn: the difference of wins between id1 and id2
        idn: a player's unique id

        The list is sorted after weight
    """
    graph = []
    for id_player1 in possible_matches:
        for id_player2 in possible_matches[id_player1]:
            graph.append((abs(wins[id_player1] - wins[id_player2]), id_player1, id_player2))

    graph.sort()
    return graph


def _get_next_matches_ids(graph):
    """ Finds next pairs of matches taking considering the win record of the players

    Args:
        graph: a list of tuples that contains every possible next match

    Returns:
        set([(weight1, id1, id2), (weight2, id3, id4), ...])

        weightn: the difference of wins between id1 and id2
        idn: a player's unique id
    """
    count_p = count_players()

    paths = []
    for i in range(len(graph)):
        count, path = find_path(graph, graph[i], count_p, [], set())
        if len(path) == (count_p / 2):
            paths.append((count, path))

    # Chose the path that has minimum weight
    paths.sort()
    chosen_path = paths[0][1]

    return chosen_path


def find_path(graph, start, nr_players, nodes, path=set(), count=0):
    """

    Args:
        graph: all possible matches
        start: chosen starting match
        nr_players: number of players
        nodes: a list with all players from chosen matches
        path: a list with chosen matches
        count: the sum of all chosen matches weights

    Returns:
        count/new_count - the sum of all chosen matches weights
        path/new_path  - a list with all matches

    """
    weight, id_player1, id_player2 = start
    nodes.append(id_player1)
    nodes.append(id_player2)
    path.add(start)
    count += weight

    if len(nodes) == nr_players:
        return count, path
    for edge in graph:
        weight1, id_player1, id_player2 = edge
        if id_player1 not in nodes and id_player2 not in nodes:
            new_count, new_path = find_path(graph, edge, nr_players, nodes, path, count)
            if new_path:
                return new_count, new_path

    return 0, set()
