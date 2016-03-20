# Tournament Results
------------------------

    * This is a Python application that uses PostgreSQL database to keep track of players
    and matches in a swiss game tournament.


# Prerequisites
---------------
1. Install Vagrant and VirtualBox

2. Clone the `fullstack-nanodegree-vm repository`

3. Clone https://github.com/orangegirl85/udacity_p2_tournament_results repository
   into fullstack/vagrant/tournament_nico


# Run App for Mac users
-----------------------
1. Launch the Vagrant VM
```
    vagrant up
    vagrant ssh
```

2. Navigate to tournament_nico folder:

`cd /vagrant/tournament_nico`


3. Import tournament.sql in order to create the database, the tables and the views for the project:

```
    psql
    \i tournament.sql
```

4. Connect in other terminal tab to the virtual machine
```
    vagrant ssh
```

5. Navigate to tournament_nico folder:

`cd /vagrant/tournament_nico`

6. Run app

`python tournament_test.py`



# Resources
----------
1. Intro to Relational Databases - Udacity course

2. `find_path` inspired by `https://www.python.org/doc/essays/graphs/`



# Extras
----------
1. Project Structure
```
/tournament_nico
    .gitignore
    Readme.md
    tournament.py
    tournament.sql
    tournament_test.py
```

2. Used unittest for testing Tournament App.

3. Prevent Rematches Functionality

4. Added generate_whole_swiss_tournament in tournament_test.py


# Other
--------

The algorithm for determining the swiss_pairings is not optimal.
The optimal next matches between players with equal or nearly-equal win record
should be determined in `find_path` not `_get_next_matches_ids`.




