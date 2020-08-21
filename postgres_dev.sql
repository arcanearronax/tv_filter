CREATE DATABASE tvapi;
CREATE USER webmaster WITH PASSWORD 'Dexter313!';
ALTER ROLE webmaster SET client_encoding TO 'utf8';
ALTER ROLE webmaster SET default_transaction_isolation TO 'read committed';
ALTER ROLE webmaster SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tvapi TO webmaster;
