#!/usr/bin/env python
#
# Test cases for tournament.py

import unittest

from tournament import *
from math import log
from psycopg2 import DatabaseError

class TournamentTestBasic(unittest.TestCase):
    def setUp(self):
        """
        Before each test we clean the database.
        We reset the matches and players.
        """
        deleteMatches()
        deletePlayers()

    def _registerPlayers(self, players):
        for player in players:
            registerPlayer(player)


class TournamentTestCount(TournamentTestBasic):
    def testCountAfterPlayersAreDeleted(self):
        """
        Test player count after players deleted.
        """
        c = self._assertCountPlayers(0, "After deletion, countPlayers should return zero.")
        self.assertNotEqual(c, '0', "countPlayers should return numeric zero, not string '0'.")
        print "1. countPlayers() returns 0 after initial deletePlayers() execution."

    def testCountAfterPlayersAreRegistered(self):
        """
        Test player count after 1 and 2 players registered.
        """
        registerPlayer("Chandra Nalaar")
        self._assertCountPlayers(1, "After one player registers, countPlayers() should be 1.")
        print "2. countPlayers() returns 1 after one player is registered."

        registerPlayer("Jace Beleren")
        self._assertCountPlayers(2, "After two players register, countPlayers() should be 2.")
        print "3. countPlayers() returns 2 after two players are registered."

        deletePlayers()
        self._assertCountPlayers(0, "After deletion, countPlayers should return zero.")
        print "4. countPlayers() returns zero after registered players are deleted.\n" \
              "5. Player records successfully deleted."

    def _assertCountPlayers(self, expected_count_players, message):
        c = countPlayers()
        self.assertEqual(c, expected_count_players, message + " Got {c}".format(c=c))

        return c


class TournamentTestStandings(TournamentTestBasic):
    def testStandingsBeforeMatches(self):
        """
        Test to ensure players are properly represented in standings prior
        to any matches being reported.
        """
        self._registerPlayers(["Melpomene Murray", "Randy Schwartz"])
        standings = playerStandings()
        self._assertStandingsLength(standings)
        self._assertStandingsValues(standings)

        print "6. Newly registered players appear in the standings with no matches."

    def _assertStandingsLength(self, standings):
        self.assertFalse(len(standings) < 2, "Players should appear in playerStandings even before "
                                             "they have played any matches.")
        self.assertFalse(len(standings) > 2, "Only registered players should appear in standings.")
        self.assertTrue(len(standings[0]) == 4, "Each playerStandings row should have four columns.")

    def _assertStandingsValues(self, standings):
        [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = standings
        self.assertTrue(matches1 == 0 and matches2 == 0, "Newly registered players should have no matches.")
        self.assertTrue(wins1 == 0 and wins2 == 0, "Newly registered players should have no wins.")
        self.assertEqual(set([name1, name2]), set(["Melpomene Murray", "Randy Schwartz"]),
                         "Registered players' names should appear in standings, "
                         "even if they have no matches played.")


class TournamentTestTReportMatches(TournamentTestBasic):
    def testReportMatches(self):
        """
        Test that matches are reported properly.
        Test to confirm matches are deleted properly.
        """
        self._registerPlayers(["Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant"])

        standings = playerStandings()
        [id1, id2, id3, id4] = [row[0] for row in standings]
        reportMatch(id1, id2)
        reportMatch(id3, id4)
        self._assertStandingsValuesAfterFirstRound(id1, id2, id3, id4)
        print "7. After a match, players have updated standings."

        deleteMatches()
        self._assertStandingsValuesAfterDeleteMatches()
        print "8. After match deletion, player standings are properly reset."
        print "9. Matches are properly deleted."

    def _assertStandingsValuesAfterFirstRound(self, id1, id2, id3, id4):
        standings = playerStandings()
        for (i, n, w, m) in standings:
            self.assertEqual(m, 1, "Each player should have one match recorded.")
            if i in (id1, id3):
                self.assertTrue(w == 1, "Each match winner should have one win recorded.")
            if i in (id2, id4):
                self.assertTrue(w == 0, "Each match loser should have zero wins recorded.")

    def _assertStandingsValuesAfterDeleteMatches(self):
        standings = playerStandings()
        self.assertEqual(len(standings), 4, "Match deletion should not change number of players in standings.")

        for (i, n, w, m) in standings:
            self.assertEqual(m, 0, "After deleting matches, players should have zero matches recorded.")
            self.assertEqual(w, 0, "After deleting matches, players should have zero wins recorded.")

class TournamentTestU(TournamentTestBasic):
    def testPairings(self):
        """
        Test that pairings are generated properly both before and after match reporting.
        """
        players = ["Twilight Sparkle", "Fluttershy", "Applejack", "Pinkie Pie", "Rarity",
                   "Rainbow Dash", "Princess Celestia", "Princess Luna"]
        self._registerPlayers(players)

        standings = playerStandings()
        [id1, id2, id3, id4, id5, id6, id7, id8] = [row[0] for row in standings]
        self._assertPairingsLength()

        self._registerMachesFirstRound(id1, id2, id3, id4, id5, id6, id7, id8)

        pairings = self._assertPairingsLength()
        self._assertPairingsAfterFirstRound(pairings, id1, id2, id3, id4, id5, id6, id7, id8)

        print "10. After one match, players with one win are properly paired."

    def _assertPairingsLength(self):
        pairings = swissPairings()
        self.assertEqual(len(pairings), 4, "For eight players, swissPairings should return 4 pairs. Got {pairs}".format(
            pairs=len(pairings)))
        return pairings

    def _registerMachesFirstRound(self, id1, id2, id3, id4, id5, id6, id7, id8):
        reportMatch(id1, id2)
        reportMatch(id3, id4)
        reportMatch(id5, id6)
        reportMatch(id7, id8)

    def _assertPairingsAfterFirstRound(self, pairings, id1, id2, id3, id4, id5, id6, id7, id8):
        [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4), (pid5, pname5, pid6, pname6),
         (pid7, pname7, pid8, pname8)] = pairings
        possible_pairs = set([frozenset([id1, id3]), frozenset([id1, id5]),
                              frozenset([id1, id7]), frozenset([id3, id5]),
                              frozenset([id3, id7]), frozenset([id5, id7]),
                              frozenset([id2, id4]), frozenset([id2, id6]),
                              frozenset([id2, id8]), frozenset([id4, id6]),
                              frozenset([id4, id8]), frozenset([id6, id8])
                              ])
        actual_pairs = set(
            [frozenset([pid1, pid2]), frozenset([pid3, pid4]), frozenset([pid5, pid6]), frozenset([pid7, pid8])])
        for pair in actual_pairs:
            self.assertIn(pair, possible_pairs, "After one match, players with one win should be paired.")

class TournamentTestZExtras(TournamentTestBasic):
    def testPreventRematches(self):
        self._registerPlayers(["Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant"])

        standings = playerStandings()
        [id1, id2, id3, id4] = [row[0] for row in standings]
        reportMatch(id1, id2)
        reportMatch(id3, id4)
        self.assertRaises(DatabaseError, reportMatch(id2, id1))
        self.assertRaises(DatabaseError, reportMatch(id2, id2))
        print "11. Rematches are properly prevented."



class SwissTournament(object):
    PLAYERS = 16

    def showEntireSwissTournament(self):
        """
        Show each round in a swiss tournament
        """
        deleteMatches()
        deletePlayers()

        i = 0
        while i < self.PLAYERS:
            registerPlayer("Player " + str(i + 1))
            i += 1
        print 'Stats before tournament:'
        self.stats()

        rounds = log(self.PLAYERS) / log(2)
        i = 0
        while i < int(rounds):
            pairings = swissPairings()
            group = {}

            j = 0
            z = 0
            while j < self.PLAYERS:
                (group['pid' + str(j)], group['pname' + str(j)], group['pid' + str(j + 1)], group['pname' + str(j + 1)]) = pairings[
                    z]
                reportMatch(group['pid' + str(j)], group['pid' + str(j + 1)])
                j += 2
                z += 1

            print ''
            print 'Stats after round:' + str(i + 1)
            first_player = self.stats()
            i += 1

        print "The winner is: " + first_player

    def stats(self):
        standings = playerStandings()
        group = {}

        j = 0
        while j < self.PLAYERS:
            (group['id' + str(j)], group['name' + str(j)], group['wins' + str(j)], group['matches' + str(j)]) = standings[j]
            j += 1

        print '----------------------------'
        print 'Id | Name | Wins | Matches'
        print '----------------------------'
        j = 0
        while j < self.PLAYERS:
            print str(group['id' + str(j)]) + " | " + str(group['name' + str(j)]) + " | " + str(
                group['wins' + str(j)]) + " | " + str(group['matches' + str(j)])
            j += 1

        return group['name0']


if __name__ == '__main__':
    tournament = SwissTournament()
    tournament.showEntireSwissTournament()
    unittest.main()
