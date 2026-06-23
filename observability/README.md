# ReelForge Observability Stack (Beginner Friendly)

This folder runs a local monitoring stack:
- Grafana (`http://localhost:3000`)
- Prometheus (`http://localhost:9090`)
- Loki (`http://localhost:3100`)
- Tempo (`http://localhost:3200`)
- Promtail (ships backend log file into Loki)

## 1. Start Backend With Monitoring Enabled
Run backend with these key env values:

```env
ENABLE_STRUCTLOG=true
LOG_FORMAT=json
ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
OTEL_INSTRUMENT_FASTAPI=true
OTEL_INSTRUMENT_HTTPX=true
OTEL_INSTRUMENT_PYMONGO=true
ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_METRICS_PATH=/metrics
```

Start backend on `http://localhost:8000`.

## 2. Start Grafana Stack
From `observability/`:

```bash
docker compose up -d
```

## 3. Open Grafana
Go to `http://localhost:3000` and login:
- user: `admin`
- password: `admin`

The following are auto-provisioned:
- Prometheus datasource
- Loki datasource
- Tempo datasource
- Dashboard: `ReelForge Backend Overview`

## 4. Generate Sample Traffic
Call a few API endpoints from browser/Postman:
- `GET http://localhost:8000/api/v1/health/live`
- `GET http://localhost:8000/api/v1/health/pools`

This creates metrics, traces, and logs for Grafana.

## 5. Where To Look In Grafana
- **Dashboard**: `ReelForge Backend Overview`
  - Request rate
  - P95 latency
  - Recent error logs
- **Explore > Tempo**
  - Search traces by service `reelforge-backend`
- **Explore > Loki**
  - Query: `{job="reelforge-backend"}`
- **Explore > Prometheus**
  - Query: `sum(rate(http_requests_total[1m])) by (handler)`

## Windows Notes
- Promtail reads local backend logs via this mount:
  - host: `../backend/logs`
  - container: `/var/log/reelforge`
- Keep backend writing logs to:
  - `backend/logs/reelforge_debug.log`

## Stop Stack
```bash
docker compose down
```

