# Docker Deployment Guide

This guide explains how to deploy Where Was Eye using Docker and Docker Compose.

## Quick Start

### Using Docker Compose (Recommended)

1. **Prepare your timeline data**:
   ```bash
   # Create data directory and copy your timeline file
   mkdir -p data
   cp /path/to/your/Location\ History.json data/location-history.json
   ```

2. **Set up environment variables**:
   ```bash
   # Copy and edit the environment file
   cp .env.example .env
   # Edit .env to add your OpenAI API key if needed
   ```

3. **Start the services**:
   ```bash
   # Start only the Where Was Eye app
   docker-compose up where-was-eye
   
   # Or start with Ollama for local LLM support
   docker-compose up
   ```

4. **Access the application**:
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health

### Using Docker Directly

1. **Build the image**:
   ```bash
   docker build -t where-was-eye .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 \
     -v $(pwd)/data:/data \
     -e LOCATION_HISTORY_PATH=/data/location-history.json \
     -e OPENAI_API_KEY=your-api-key-here \
     where-was-eye
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOCATION_HISTORY_PATH` | Path to Google Timeline JSON | `/data/location-history.json` | Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT integration | - | No |
| `OLLAMA_HOST` | Ollama server host | `http://host.docker.internal:11434` | No |
| `SERVER_HOST` | Server bind address | `0.0.0.0` | No |
| `SERVER_PORT` | Server port | `8000` | No |

### Volume Mounts

- **`/data`**: Directory containing your timeline data file
- **`/app/logs`**: Application logs (optional)

## Production Deployment

### Using Docker Compose in Production

1. **Create a production environment file**:
   ```bash
   cp .env.example .env.production
   # Edit with production values
   ```

2. **Run in detached mode**:
   ```bash
   docker-compose --env-file .env.production up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

### Using Docker Swarm/Kubernetes

For production deployments, you can use the Docker image with orchestration tools:

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: where-was-eye
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: where-was-eye
        image: your-registry/where-was-eye:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOCATION_HISTORY_PATH
          value: "/data/location-history.json"
        volumeMounts:
        - name: timeline-data
          mountPath: /data
      volumes:
      - name: timeline-data
        persistentVolumeClaim:
          claimName: timeline-pvc
```

## Troubleshooting

### Common Issues

1. **Timeline file not found**:
   ```bash
   # Ensure the file exists and is mounted correctly
   docker exec -it container-name ls -la /data
   ```

2. **Permission issues**:
   ```bash
   # Check file permissions
   docker exec -it container-name ls -la /data/location-history.json
   ```

3. **Ollama connection issues**:
   - Use `host.docker.internal` on Docker Desktop
   - Use the actual IP address on Linux

4. **Build failures**:
   ```bash
   # Clear build cache
   docker-compose build --no-cache
   ```

### Health Checks

The container includes health checks that verify the API is responsive:
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' container-name

# Manual health check
curl http://localhost:8000/health
```

## Monitoring

### Logs
```bash
# View logs
docker-compose logs where-was-eye

# Follow logs
docker-compose logs -f where-was-eye

# View specific container logs
docker logs container-name
```

### Metrics
The application exposes standard metrics on the health endpoint and can be integrated with monitoring tools like:
- Prometheus
- Grafana
- Datadog

## Security Considerations

1. **Use secrets for API keys**:
   ```bash
   # Instead of environment variables, use Docker secrets
   echo "your-api-key" | docker secret create openai_api_key -
   ```

2. **Network security**:
   - Expose only necessary ports
   - Use internal networks for inter-container communication

3. **Regular updates**:
   - Keep the base image updated
   - Regularly update dependencies