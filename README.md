# Tournament Results
------------------------

    * This is a Python application that uses PostgreSQL database to keep track of players
    and matches in a game tournament.


# Prerequisites
---------------
1. Install Vagrant and VirtualBox

2. Clone the `fullstack-nanodegree-vm repository`

3. Clone https://github.com/orangegirl85/udacity_p2_tournament_results repository
   into fullstack/vagrant/tournament_nico


# Run App for Mac users
-----------------------
1. Launch the Vagrant VM

2. Navigate to tournament_nico folder: cd /vagrant/tournament_nico

3. Create database and tables for the project:

```
   psql

   CREATE DATABASE tournament;

   \c tournament

   \i tournament.sql
```


# Resources
----------
1. Intro to Relational Databases - Udacity course

2. swissPairings functionality inspired by
  `http://stackoverflow.com/questions/19218458/how-to-retrieve-even-rows-in-a-table`


# Extras
----------
1. Project Structure
```
/tournament_nico
    tournament.py
    tournament.sql
    tournament_test.py
    .gitignore
    Readme.md
```

2. Used unittest for testing Tournament App.

3. Prevent Rematches Functionality



