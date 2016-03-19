#!/usr/bin/env python
"""Test cases for tournament.py."""

import unittest

from tournament import delete_matches, delete_players, register_player, \
    count_players, player_standings, swiss_pairings, report_match

from math import log
from psycopg2 import DatabaseError


class TournamentTestBasic(unittest.TestCase):
    """Basic Tournament Class."""

    def setUp(self):
        """Clean database before each test.

        Reset the matches and players.
        """
        delete_matches()
        delete_players()

    def _register_players(self, players):
        """Register a list of players in the database.

        Args:
            players

        """
        for player in players:
            register_player(player)


class TournamentTestCount(TournamentTestBasic):
    """Tournament Test Count."""

    def test_count_after_players_are_deleted(self):
        """Test player count after players are deleted."""
        c = self._assert_count_players(
            0, "After deletion, count_players should return zero.")
        msg_error = "count_players should return numeric zero, not string '0'."
        self.assertNotEqual(c, '0', msg_error)
        msg = "1. count_players() returns 0 after initial"
        print msg + " delete_players() execution."

    def test_count_after_players_are_registered(self):
        """Test player count after 1 and 2 players registered."""
        register_player("Chandra Nalaar")
        self._assert_count_players(
            1, "After one player registers, count_players() should be 1.")
        print "2. count_players() returns 1 after one player is registered."

        register_player("Jace Beleren")
        self._assert_count_players(
            2, "After two players register, count_players() should be 2.")
        print "3. count_players() returns 2 after two players are registered."

        delete_players()
        self._assert_count_players(
            0, "After deletion, count_players should return zero.")
        msg = "4. count_players() returns zero after "
        print msg + "registered players are deleted.\n" \
            "5. Player records successfully deleted."

    def _assert_count_players(self, expected_count_players, message):
        c = count_players()
        self.assertEqual(c, expected_count_players,
                         message + " Got {c}".format(c=c))

        return c


class TournamentTestStandings(TournamentTestBasic):
    """Tournament Standings Test."""

    def test_standings_before_matches(self):
        """Test to ensure players are properly represented in standings.

        Standings are analysed prior to any matches being reported.
        """
        self._register_players(["Melpomene Murray", "Randy Schwartz"])
        standings = player_standings()
        self._assert_standings_length(standings)
        self._assert_standings_values(standings)
        msg = "6. Newly registered players appear"
        print msg + " in the standings with no matches."

    def _assert_standings_length(self, standings):
        self.assertFalse(len(standings) < 2, "Players should appear in \
            playerStandings even before they have played any matches.")
        self.assertFalse(len(standings) > 2,
                         "Only registered players should appear in standings.")
        self.assertTrue(
            len(standings[0]) == 4, "Each playerStandings row should have four \
             columns.")

    def _assert_standings_values(self, standings):
        [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = \
            standings
        self.assertTrue(matches1 == 0 and matches2 == 0,
                        "Newly registered players should have no matches.")
        self.assertTrue(wins1 == 0 and wins2 == 0,
                        "Newly registered players should have no wins.")
        self.assertEqual(set([name1, name2]),
                         set(["Melpomene Murray", "Randy Schwartz"]),
                         "Registered players' names should appear in standings, \
            even if they have no matches played.")


class TournamentTestTReportMatches(TournamentTestBasic):
    """Tournament Report Matches Test."""

    def test_report_matches(self):
        """Test that matches are reported properly.

        Test to confirm matches are deleted properly.
        """
        self._register_players(
            ["Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant"])

        standings = player_standings()
        [id1, id2, id3, id4] = [row[0] for row in standings]
        report_match(id1, id2)
        report_match(id3, id4)
        self._assert_standings_values_after_first_round(id1, id2, id3, id4)
        print "7. After a match, players have updated standings."

        delete_matches()
        self._assert_standings_values_after_delete_matches()
        print "8. After match deletion, player standings are properly reset."
        print "9. Matches are properly deleted."

    def _assert_standings_values_after_first_round(self, id1, id2, id3, id4):
        standings = player_standings()
        for (i, n, w, m) in standings:
            self.assertEqual(
                m, 1, "Each player should have one match recorded.")
            if i in (id1, id3):
                self.assertTrue(
                    w == 1, "Each match winner should have one win recorded.")
            if i in (id2, id4):
                self.assertTrue(
                    w == 0, "Each match loser should have zero wins recorded.")

    def _assert_standings_values_after_delete_matches(self):
        standings = player_standings()
        self.assertEqual(len(
            standings), 4, "Match deletion should not change number of players \
                 in standings.")

        for (i, n, w, m) in standings:
            self.assertEqual(
                m, 0, "After deleting matches, players should have zero matches \
                 recorded.")
            self.assertEqual(
                w, 0, "After deleting matches, players should have zero wins \
                recorded.")


class TournamentTestUPairings(TournamentTestBasic):
    """Tournament Pairings Test."""

    def test_pairings(self):
        """Test that pairings are generated properly.

        Test this before and after match reporting.
        """
        players = ["Twilight Sparkle", "Fluttershy", "Applejack", "Pinkie Pie",
                   "Rarity", "Rainbow Dash", "Princess Celestia",
                   "Princess Luna"]
        self._register_players(players)

        standings = player_standings()
        [id1, id2, id3, id4, id5, id6, id7, id8] = [row[0]
                                                    for row in standings]
        self._assert_pairings_length()

        self._register_first_round(id1, id2, id3, id4, id5, id6, id7, id8)

        pairings = self._assert_pairings_length()
        self._assert_pairings_after_first_round(
            pairings, id1, id2, id3, id4, id5, id6, id7, id8)

        print "10. After one match, players with one win are properly paired."

    def _assert_pairings_length(self):
        pairings = swiss_pairings()
        self.assertEqual(len(pairings), 4, "For eight players, swissPairings \
            should return 4 pairs. Got {pairs}".format(
            pairs=len(pairings)))
        return pairings

    def _register_first_round(self, id1, id2, id3, id4, id5, id6, id7, id8):
        report_match(id1, id2)
        report_match(id3, id4)
        report_match(id5, id6)
        report_match(id7, id8)

    def _assert_pairings_after_first_round(self, pairings, id1, id2, id3, id4,
                                           id5, id6, id7, id8):
        [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4),
         (pid5, pname5, pid6, pname6), (pid7, pname7, pid8, pname8)] = pairings
        possible_pairs = set([frozenset([id1, id3]), frozenset([id1, id5]),
                              frozenset([id1, id7]), frozenset([id3, id5]),
                              frozenset([id3, id7]), frozenset([id5, id7]),
                              frozenset([id2, id4]), frozenset([id2, id6]),
                              frozenset([id2, id8]), frozenset([id4, id6]),
                              frozenset([id4, id8]), frozenset([id6, id8])
                              ])
        actual_pairs = set(
            [frozenset([pid1, pid2]), frozenset([pid3, pid4]),
                frozenset([pid5, pid6]), frozenset([pid7, pid8])])
        for pair in actual_pairs:
            self.assertIn(
                pair, possible_pairs, "After one match, players with one win \
                should be paired.")


class TournamentTestZExtras(TournamentTestBasic):
    """Tournament Test Extras."""

    def test_prevent_rematches(self):
        """Test that the system does not allow rematches.

        Test that the system prevent matches between a player and himself.
        """
        self._register_players(
            ["Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant"])

        standings = player_standings()
        [id1, id2, id3, id4] = [row[0] for row in standings]
        report_match(id1, id2)
        report_match(id3, id4)
        self.assertRaises(DatabaseError, report_match(id2, id1))
        self.assertRaises(DatabaseError, report_match(id2, id2))
        print "11. Rematches are properly prevented."


class SwissTournament(object):
    """Swiss Tournament display."""

    NR_OF_PLAYERS = 16

    def generate_whole_swiss_tournament(self):
        """Display each round statistics in a swiss tournament.

        Display winner's name.
        """
        # clean database
        delete_matches()
        delete_players()

        print '\n\nSWISS TOURNAMENT FOR {0} PLAYERS:'.format(
            self.NR_OF_PLAYERS)

        # register {NR_OF_PLAYERS} players
        i = 0
        while i < self.NR_OF_PLAYERS:
            register_player("Player " + str(i + 1))
            i += 1

        # calculate nr of rounds necessary to determine a winner
        rounds = log(self.NR_OF_PLAYERS) / log(2)
        i = 0
        while i < int(rounds):
            # determine next round matches
            pairings = swiss_pairings()
            group = {}

            j = 0
            z = 0
            # register next round matches
            while j < self.NR_OF_PLAYERS:
                (group['pid' + str(j)], group['pname' + str(j)],
                 group['pid' + str(j + 1)],
                 group['pname' + str(j + 1)]) = pairings[z]
                report_match(group['pid' + str(j)], group['pid' + str(j + 1)])
                j += 2
                z += 1

            print '\nStats after round: ' + str(i + 1)

            # show round statistics
            first_player = self.stats()
            print '\n'
            i += 1

        print "-------------------------"
        print "THE WINNER IS: " + first_player + "."
        print "-------------------------\n\n"

    def stats(self):
        """Display player_standings.

         Id | Name | Wins | Matches
         1 | Player 1 | 1 | 1
         2 | Player 2 | 0 | 1

        Returns:
            first player's name
        """
        standings = player_standings()

        print '----------------------------'
        print 'Id | Name | Wins | Matches'
        print '----------------------------'
        j = 0
        while j < self.NR_OF_PLAYERS:
            print str(standings[j][0]) + " | " + str(standings[j][1]) + " | " \
                + str(standings[j][2]) + " | " + str(standings[j][3])
            j += 1

        return standings[0][1]


if __name__ == '__main__':
    tournament = SwissTournament()
    tournament.generate_whole_swiss_tournament()
    unittest.main()
