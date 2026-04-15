#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8080}"
API_URL="${API_URL:-http://localhost:8000}"
MINIO_URL="${MINIO_URL:-http://localhost:9001}"
SEARCH_URL="${SEARCH_URL:-http://localhost:9200}"

check_json_field() {
  local url="$1"
  local path="$2"
  python3 - "$url" "$path" <<'PY'
import json
import sys
from urllib.request import urlopen

url, path = sys.argv[1], sys.argv[2]
data = json.load(urlopen(url, timeout=10))
value = data
for key in path.split("."):
    value = value[key]
print(value)
PY
}

echo "[1/8] Docker Compose services"
docker compose -f "$ROOT_DIR/docker-compose.yml" ps

echo "[2/8] Gateway health"
curl -fsS "$BASE_URL/health" >/dev/null
echo "  ok -> $BASE_URL/health"

echo "[3/8] API health"
curl -fsS "$API_URL/health" >/dev/null
echo "  ok -> $API_URL/health"

echo "[4/8] Product list"
PRODUCT_COUNT="$(python3 - "$API_URL/api/products" <<'PY'
import json
import sys
from urllib.request import urlopen

data = json.load(urlopen(sys.argv[1], timeout=10))
print(len(data["data"]))
PY
)"
echo "  products -> $PRODUCT_COUNT"

echo "[5/8] Recommendations"
RECOMMENDATION_COUNT="$(python3 - "$API_URL/api/recommendations/home" <<'PY'
import json
import sys
from urllib.request import urlopen

data = json.load(urlopen(sys.argv[1], timeout=10))
print(len(data["data"]["items"]))
PY
)"
echo "  recommendations -> $RECOMMENDATION_COUNT"

echo "[6/8] MinIO console"
curl -fsS "$MINIO_URL" >/dev/null
echo "  ok -> $MINIO_URL"

echo "[7/8] OpenSearch cluster health"
SEARCH_STATUS="$(check_json_field "$SEARCH_URL/_cluster/health" "status")"
echo "  status -> $SEARCH_STATUS"

echo "[8/8] Admin platform ops"
python3 - "$API_URL" <<'PY'
import json
import sys
from urllib.request import Request, urlopen

base = sys.argv[1]
login_req = Request(
    base + "/api/auth/login",
    data=json.dumps({"email": "admin@example.com", "password": "Admin123!"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
login_data = json.load(urlopen(login_req, timeout=10))
token = login_data["data"]["access_token"]
ops_req = Request(
    base + "/api/admin/platform/ops",
    headers={"Authorization": f"Bearer {token}"},
)
ops_data = json.load(urlopen(ops_req, timeout=10))["data"]
ready = {item["name"]: item["status"] for item in ops_data["readiness"]}
assert ready["database"] == "READY"
assert ready["redis"] == "READY"
assert ready["async_tasks"] == "READY"
assert ready["storage"] == "READY"
assert ready["search"] == "READY"
print("  admin platform ops -> ready")
PY

echo
echo "Smoke checks passed."
