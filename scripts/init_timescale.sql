-- This script runs during PostgreSQL initialization
-- It only installs the TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
