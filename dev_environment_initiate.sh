# Need to prompt for path of virtualenv
VENV_CONFIG_SCRIPT="./venv/bin/activate"

# Need to check and see if these are already set, handle differently if true
echo "" >> $VENV_CONFIG_SCRIPT
echo "export SKEY='f6xa0$&!oi(r^7pi7dsku!u+8=%36y(byaiigbqt*maop1h%)j' # development secret key" >> $VENV_CONFIG_SCRIPT
echo "export HostName='tvapi.arcanedomain.duckdns.org' # primary host" >> $VENV_CONFIG_SCRIPT
echo "export UserName='password' # username for the database user" >> $VENV_CONFIG_SCRIPT
echo "export UserPass='username' # username for the database user" >> $VENV_CONFIG_SCRIPT

# Need to bail out for now
exit

# Check if requirements are installed, with required versions
#sudo dnf install python3-pip python3-dev postgresql-libs postgresql postgresql-contrib

# Check if Postgres is installed, with minimum version


# Prompt for update, install, or bypass


# Run setup script for postgres
sudo postgresql-setup initdb
sudo systemctl enable --now postgresql
SQL_SCRIPT="postgres_dev.sql"
DATABASE_NAME="tvapi"
PSQL_USER="username"
PSQL_PASS="password"
echo "CREATE DATABASE $DATABASE_NAME;" > $SQL_SCRIPT
echo "CREATE USER $PSQL_USER WITH PASSWORD '$PSQL_PASS';" >> $SQL_SCRIPT
echo "ALTER ROLE $PSQL_USER SET client_encoding TO 'utf8';" >> $SQL_SCRIPT
echo "ALTER ROLE $PSQL_USER SET default_transaction_isolation TO 'read committed';" >> $SQL_SCRIPT
echo "ALTER ROLE $PSQL_USER SET timezone TO 'EST';" >> $SQL_SCRIPT
echo "GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $PSQL_USER;" >> $SQL_SCRIPT
sudo -u postgres psql -a -f $SQL_SCRIPT
