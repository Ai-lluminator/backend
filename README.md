# Sentence Transformer-based Science Paper Bot Backend

## Overview

This repository contains the backend for a Retrieval-Augmented Generation (RAG) based system that filters and delivers science papers based on user-defined prompts. The system continuously updates the user on new scientific papers from selected data sources (arXiv, PubMed, AISel) and communicates through a Telegram bot. The backend manages the data pipeline, user interactions, and automatic updates, making use of Docker for easy deployment.

## Key Features

- **Data Sources**: Integrated with popular scientific databases (arXiv, PubMed, AISel) for filtering papers based on user queries.
- **Telegram Bot**: Supports a bot to interact with users, delivering new papers directly to their Telegram account.
- **Automatic Updates**: Regular updates via a cron job to ensure users receive the latest research papers.
- **Database Initialization**: Initializes and manages the underlying database using SQL scripts.
- **Docker Support**: Streamlined setup and deployment using Docker and Docker Compose.

## Repository Structure

```
backend/
├── data-sources/                -- Handles integration with scientific databases
│   ├── aisel/                   -- AISel crawler
│   ├── arxiv/                   -- arXiv crawler
│   └── pubmed/                  -- PubMed crawler
├── database_init/               -- Contains SQL scripts for initializing the database
│   └── init.sql                 -- Database schema setup script
├── ollama/                      -- Manages Ollama service integration
│   └── DOCKERFILE               -- Dockerfile for Ollama service
├── telegram/                    -- Manages the Telegram bot service
│   ├── handlers/                -- Bot command and response handlers
│   ├── telegram_handler.py      -- Main bot interaction script
│   ├── DOCKERFILE               -- Dockerfile for Telegram bot
│   └── requirements.txt         -- Python dependencies for Telegram bot
├── telegram_update/             -- Manages periodic updates for Telegram and data sources
│   ├── crontab                  -- Cron job configuration for updates
│   ├── helper.py                -- Utility functions for updates
│   ├── updater.py               -- Script to fetch new papers
│   ├── DOCKERFILE               -- Dockerfile for update service
│   └── requirements.txt         -- Python dependencies for the update service
├── .env.template                -- Environment variable file
├── .gitignore                   -- Git ignore file for version control
├── database.py                  -- Script for database interaction
├── docker-compose.yaml          -- Docker Compose configuration for managing containers
└── README.md                    -- Project documentation
```

  
## Requirements

- **Docker**: Ensure you have Docker installed on your system. You can download it [here](https://www.docker.com/get-started).
- **Python**: For local development, ensure Python 3.8+ is installed.

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone[ https://github.com/Ai-lluminator/backend/
   cd backend
   ```

2. **Set up environment variables**:
   Copy the `.env.example` file to `.env` and update the necessary configurations like database credentials, Telegram API token, etc.

3. **Build and start the services**:
   Run the following command to start the backend using Docker Compose:
   ```bash
   docker-compose -f docker-compose.yaml up
   ```

4. **Interact with the system**:
   Once the containers are up, the Telegram bot will be available to start receiving and responding to user prompts.

## Updating the Users

The `telegram_update` service runs once per day (defined in `crontab`) to fetch new papers from the database and send relevant ones to the users. You can customize the frequency of updates by modifying the `crontab` file.

## Contributing

1. Fork the repo.
2. Create a new feature branch.
3. Commit your changes.
4. Push to the branch.
5. Create a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.