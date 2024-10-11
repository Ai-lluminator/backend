-- Create a new database
CREATE DATABASE database_ailluminator;

\connect database_ailluminator;

CREATE EXTENSION IF NOT EXISTS vector;

-- Create the 'users' table
CREATE TABLE IF NOT EXISTS users (
    id                     SERIAL PRIMARY KEY,
    telegram_id            INTEGER,
    chat_id                INTEGER,
    created_at             TIMESTAMP DEFAULT NOW()
);

-- Create the 'prompts' table
CREATE TABLE IF NOT EXISTS prompts (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    prompt     TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    activate   BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create the 'messages_sent' table
CREATE TABLE IF NOT EXISTS messages_sent (
    id         SERIAL PRIMARY KEY,
    timestamp  TIMESTAMP DEFAULT NOW(),
    user_id    INTEGER NOT NULL,
    num_papers INTEGER NOT NULL
);

-- Create the 'papers' table
CREATE TABLE IF NOT EXISTS papers (
    id          SERIAL PRIMARY KEY,
    link         TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    title       TEXT,
    content     TEXT,
    embedding   vector(384)
);

-- Create the 'paper_in_mesage' table
CREATE TABLE IF NOT EXISTS paper_in_message (
    message_id INTEGER NOT NULL,
    paper_id   INTEGER NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages_sent (id),
    FOREIGN KEY (paper_id) REFERENCES papers (id)
);
-- Output message for successful database initialization
DO $$ 
BEGIN 
  RAISE NOTICE 'Database and tables have been successfully created.';
END $$;
