# POLITIQUES DE FIABILITÉ - CLIENT API

## 1. TIMEOUTS PAR SERVICE

| Service | Endpoint | Connection | Read | Total |
|---------|----------|------------|------|-------|
| Auth | POST /auth/login | 3s | 5s | 8s |
| Auth | POST /auth/logout | 3s | 3s | 6s |
| Documents | GET /documents | 5s | 10s | 15s |
| Documents | POST /documents | 5s | 15s | 20s |
| Documents | GET /documents/{id} | 5s | 10s | 15s |
| Documents | PUT /documents/{id} | 5s | 10s | 15s |
| Documents | DELETE /documents/{id} | 5s | 8s | 13s |
| Search | GET /search | 5s | 8s | 13s |

## 2. CONFIGURATION DES RETRY

```python
RETRY_CONFIG = {
    'max_retries': 3,
    'base_delay': 1.0,
    'max_delay': 30.0,
    'jitter': True,
    'retryable_statuses': [500, 502, 503, 504, 429]
}