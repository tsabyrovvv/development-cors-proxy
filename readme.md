# FastAPI CORS Proxy

A simple asynchronous CORS proxy built with FastAPI and HTTPX.  
It allows making cross-origin requests to external URLs with optional environment-based configuration.

## Features
- **CORS enabled** for multiple origins
- **Configurable** via environment variables
- **Asynchronous** requests with `httpx`
- **Docker support**

## Environment Variables
| Variable          | Default Value        | Description |
|-------------------|----------------------|-------------|
| `HOST`            | `0.0.0.0`           | Host address for the server |
| `PORT`            | `8000`              | Port number for the server |
| `TIMEOUT`         | `30`                | Request timeout (seconds) |
| `ALLOWED_ORIGINS` | `*`                  | Comma-separated list of allowed origins |

Example `.env` file:
```env
HOST=0.0.0.0
PORT=8000
TIMEOUT=20
ALLOWED_ORIGINS=http://localhost:3000,https://example.com
```

Example `.env` file:
```python
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Docker Using:
```docker
docker build -t fastapi-proxy .
docker run -d --env-file .env -p 8000:8000 fastapi-proxy
```

API Usage:
```shell
GET /?url=https://example.com
```
```curl
curl "http://localhost:8000/?url=https://example.com"
```
