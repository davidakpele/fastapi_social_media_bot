# Social Media Bot

A Dockerized FastAPI application for managing social media accounts, scheduling posts, and handling WebSocket connections.

## Features

- FastAPI backend with JWT authentication
- PostgreSQL database for persistent storage
- Redis for caching and queues
- WebSocket support for real-time updates
- Nginx as a reverse proxy
- Dockerized environment for easy deployment

## Requirements

- Docker & Docker Compose
- `.env` file with configuration variables

## Setup

1. **Build Docker containers**:

```bash
docker-compose build
```
2. Initialize the database:

```bash
docker-compose run --rm db_init
```
4. Start the full stack:
```bash
docker-compose up
```
### Notes
- Run db_init only once to create tables.
- Nginx is configured as a reverse proxy with WebSocket support.
- Use docker-compose down -v to remove containers and volumes if needed.


### CI/CD HELP

## 🚀 Deployment & Docker Commands

- These commands provide guidance for deploying and managing the application using Docker, Docker Compose, and server services like Apache.

### Start & Build Containers
```bash
docker-compose up -d                     # Start containers in detached mode
docker-compose up --build -d             # Build and start containers
docker-compose up --build -d --remove-orphans  # Build, start, and remove orphaned containers
docker-compose build --no-cache          # Build containers without cache
```

### Stop & Clean Up Containers
```bash
docker-compose down -v                   # Stop and remove containers and volumes
docker-compose down -v --rmi all         # Stop containers, remove volumes, remove images
docker system prune -a --volumes         # Clean all unused Docker objects including volumes
docker system prune -a                    # Clean all unused Docker objects excluding volumes
docker-compose down && docker-compose up -d --build  # Rebuild and restart containers
```

### Service Management

```bash
sudo systemctl restart apache2           # Restart Apache server
docker-compose up -d db                  # Start only the database container
docker-compose ps                        # List running containers
docker-compose restart web               # Restart the web container
```

### Logs & Debugging
```bash
docker logs httpdocs-web-1               # View container logs
docker logs httpdocs-web-1 2>&1 | grep -i error  # Filter logs for errors
```
### Docker Cleanup & Inspection
```bash
docker network prune                      # Remove unused Docker networks
docker volume ls                          # List Docker volumes
docker exec -it nginx nginx -t           # Test Nginx configuration inside container
````
