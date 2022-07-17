# weeelab-telegram-bot
[![License](http://img.shields.io/:license-GPL3.0-blue.svg)](http://www.gnu.org/licenses/gpl-3.0.html)

WEEE Open Telegram bot.

The goal of this bot is to obtain information about who is currently in the lab,  
who has done what, compute some stats and, in general, simplify the life of our members...  
And to avoid waste of paper as well.  

Data comes from

* a PostgreSQL database
* the [tarallo](https://github.com/WEEE-Open/tarallo) inventory management system
* a LDAP server

## Installation

`weeelab_bot.py` is the main script, and it requires a lot of enviroment variables.
Some of them are located in the .env file, like:

* `TOKEN_BOT`: Telegram token for the bot API
* `POSTGRES_USER`: Postgres user name 
* `POSGRES_PASSWD`: Postrgres user password
* `POSTGRES_DATABASE`: Postgres database name

See `variables.py` for the others.

## Command syntax

`/start` the bot and type `/[COMMAND] [OPTION]`.  

Available commands and options:

- `/inlab` - Show the people in lab
- `/log` - Show log of the selected day
- `/log all` - Show last 31 days worth of logs
- `/ring` - Ring the bell
- `/stat` - Show hours you've spent in lab
- `/history item` - Show history for an item, straight outta T.A.R.A.L.L.O.
- `/history item n` - Show n history entries

Only for admin users
- `/stat name.surname` - Show hours spent in lab by this user
- `/top` - Show a list of top users by hours spent this month
- `/top all` - Show a list of top users by hours spent

## Developers setup
First you need to install postgreSQL on your machine, create the user `weeelab_bot` and the `weeelab` database. Execute the following commands:

```
~ sudo apt install postgresql
~ sudo service postgresql start 
~ sudo -u postgres psql
```

Inside the postgreSQL shell, change the default user password with:

```
postgres=# \password postgres
--- change password ---
postgres=# \q
```

Then, we need to create the user weeelab_bot:

```
~ sudo adduser weeelab_bot
~ sudo passwd weeelab_bot
--- change password ---
~ sudo -u postgres createuser --interactive
--- create user 'weeelab_bot' saying no to all the questions ---
```

Make sure that the individual user passwords are the same on the system and on postgreSQL.

Now, we need to create the `weeelab` database and load the default tables:

```
~ sudo -u postgres createdb weeelab
~ sudo -u postgres psql weeelab < weeelab.sql
~ sudo -u postgres psql
postgres=# \c weeelab
postgres=# GRANT ALL PRIVILEGES ON log_raw TO weeelab_bot;
postgres=# GRANT ALL PRIVILEGES ON log TO weeelab_bot;
postgres=# \q
```

Now set up your Python development environment using the `requirements.txt` file provided by this repository.

You may need to setup the `.env` file with all the environment parameters.