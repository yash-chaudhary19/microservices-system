-- Create individual databases for microservices to enforce strict database-per-service isolation
CREATE DATABASE users_db;
CREATE DATABASE notifications_db;

-- Grant privileges to the default user
GRANT ALL PRIVILEGES ON DATABASE users_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE notifications_db TO postgres;
