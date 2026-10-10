#!/bin/bash
# QA 124-127 on a clean copy with no instance database.
# The local-address check reads ss column 4 only. The peer column is
# "0.0.0.0:*" and must not be treated as the bind address.
# set -e is on. The EXIT trap still runs the "nothing listens" check.

set -euo pipefail

ROOT="/workspace/hot-room-log-rc3"
PY="$ROOT/.venv/bin/python"
CLEAN="/tmp/hrl-rc4/clean"
LOGDIR="$ROOT/review/rc4/evidence/http"
LOG="$LOGDIR/qa-124-127.log"
mkdir -p "$LOGDIR"
: > "$LOG"

exec > >(tee -a "$LOG") 2>&1

echo "QA 124-127 started $(date -Is)"
unset HOTROOM_DB || true
unset HOTROOM_READONLY || true
unset PORT || true
unset HOST || true
fail=0
SRV=""

say_fail() {
  echo "FAIL $*"
  fail=1
}

cleanup_server() {
  if [[ -n "${SRV}" ]]; then
    kill "$SRV" 2>/dev/null || true
    wait "$SRV" 2>/dev/null || true
    SRV=""
  fi
  # Only stop servers started from this clean copy.
  if [[ -d "$CLEAN" ]]; then
    pkill -f "$CLEAN/app.py" 2>/dev/null || true
  fi
  sleep 0.3
}

# Local address is field 4. Do not match the peer field.
local_addrs_for() {
  local port="$1"
  ss -ltn | awk -v port="$port" 'NR>1 && $4 ~ (":" port "$") { print $4 }'
}

final_port_check() {
  set +e
  echo "=== after stop: listeners whose local address is :5050 or :5051 ==="
  ss -ltn | awk 'NR==1 || ($4 ~ /:5050$/ || $4 ~ /:5051$/)'
  local left
  left="$(ss -ltn | awk 'NR>1 && ($4 ~ /:5050$/ || $4 ~ /:5051$/) { print $4 }')"
  if [[ -n "$left" ]]; then
    echo "FAIL residual local listeners:"
    echo "$left"
    echo "$left" > "$LOGDIR/residual-listeners.txt"
    echo "residual_fail=1" > "$LOGDIR/residual-status.txt"
    residual_fail=1
  else
    echo "PASS nothing listens on 5050 or 5051"
    echo "none" > "$LOGDIR/residual-listeners.txt"
    echo "residual_fail=0" > "$LOGDIR/residual-status.txt"
    residual_fail=0
  fi
  set -e
}

on_exit() {
  local status=$?
  trap - EXIT
  set +e
  cleanup_server
  final_port_check
  if [[ "${residual_fail:-1}" -ne 0 ]]; then
    status=1
  fi
  if [[ "$fail" -ne 0 ]]; then
    status=1
  fi
  echo "QA 124-127 exit $status"
  exit "$status"
}
trap on_exit EXIT

echo "=== clean copy ==="
rm -rf "$CLEAN"
mkdir -p "$CLEAN"
# tar, not rsync: rsync is not installed on this machine.
tar -C "$ROOT" \
  --exclude .venv \
  --exclude instance \
  --exclude __pycache__ \
  --exclude review \
  --exclude .git \
  -cf - . | tar -C "$CLEAN" -xf -
if [[ -e "$CLEAN/instance/hotroom.db" ]]; then
  say_fail "clean copy already has instance/hotroom.db"
  exit 1
fi
echo "pip install"
"$PY" -m pip install -r "$CLEAN/requirements.txt"

start_server() {
  local logfile="$1"
  shift
  cleanup_server
  (
    cd "$CLEAN"
    # exec so the recorded pid is the server, not a shell wrapper.
    exec "$@" "$PY" app.py
  ) > "$logfile" 2>&1 &
  SRV=$!
  local i
  for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    if grep -q "Running on" "$logfile" 2>/dev/null; then
      return 0
    fi
    if ! kill -0 "$SRV" 2>/dev/null; then
      echo "server exited early"
      cat "$logfile"
      return 1
    fi
    sleep 0.25
  done
  echo "server did not print Running on"
  cat "$logfile"
  return 1
}

echo "=== 124 first start ==="
if start_server "$LOGDIR/http-5050.log"; then
  echo "PASS server process started"
else
  say_fail "124 server did not start"
fi
echo "--- flask log ---"
cat "$LOGDIR/http-5050.log"
echo "--- ss local column for 5050 (peer ignored) ---"
ss -ltn | awk 'NR==1 || $4 ~ /:5050$/ || $5 ~ /:5050/'
locals="$(local_addrs_for 5050 || true)"
echo "local addresses: ${locals:-<none>}"
if [[ "$locals" == "127.0.0.1:5050" ]]; then
  echo "PASS 124 bind 127.0.0.1:5050"
else
  say_fail "124 bind expected 127.0.0.1:5050 got [${locals}]"
fi
if [[ -f "$CLEAN/instance/hotroom.db" ]]; then
  echo "PASS 124 instance/hotroom.db created"
else
  say_fail "124 database was not created"
fi
code="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5050/ || true)"
echo "GET / -> $code"
if [[ "$code" == "200" ]]; then
  echo "PASS 124 GET / 200"
else
  say_fail "124 GET / $code"
fi
rooms="$(curl -s http://127.0.0.1:5050/api/rooms || true)"
echo "GET /api/rooms -> $rooms"
count="$(printf '%s' "$rooms" | "$PY" -c 'import json,sys; print(len(json.load(sys.stdin)))' 2>/dev/null || echo 0)"
if [[ "$count" == "3" ]]; then
  echo "PASS 124 three rooms"
else
  say_fail "124 room count $count"
fi

echo "=== 125 create room, restart, data persists ==="
headers="$LOGDIR/post-room.headers"
curl -s -D "$headers" -o /dev/null -X POST -d "name=Curl Room" http://127.0.0.1:5050/rooms || true
echo "--- POST headers ---"
cat "$headers"
status_line="$(awk 'NR==1 { print }' "$headers")"
location="$(awk 'tolower($1)=="location:" { print $2 }' "$headers" | tr -d '\r')"
echo "status [$status_line] location [$location]"
if [[ "$status_line" == *"302"* && "$location" == */rooms/4 ]]; then
  echo "PASS 125 302 to /rooms/4"
else
  say_fail "125 POST status/location"
fi
cleanup_server
if start_server "$LOGDIR/http-5050b.log"; then
  echo "PASS 125 restarted"
else
  say_fail "125 restart failed"
fi
rooms="$(curl -s http://127.0.0.1:5050/api/rooms || true)"
echo "$rooms" > "$LOGDIR/rooms-after-restart.json"
if printf '%s' "$rooms" | "$PY" -c 'import json,sys; rooms=json.load(sys.stdin); assert len(rooms)==4; assert any(r["name"]=="Curl Room" for r in rooms)'; then
  echo "PASS 125 four rooms including Curl Room"
else
  say_fail "125 persistence"
fi

echo "=== 126 static, missing, export ==="
css="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5050/static/style.css || true)"
nope="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5050/nope || true)"
curl -s -D "$LOGDIR/export.headers" -o "$LOGDIR/export.body" http://127.0.0.1:5050/export.csv || true
echo "css $css nope $nope"
echo "--- export headers ---"
cat "$LOGDIR/export.headers"
if [[ "$css" == "200" && "$nope" == "404" ]] && grep -qi "text/csv" "$LOGDIR/export.headers" && grep -qi "attachment" "$LOGDIR/export.headers"; then
  echo "PASS 126"
else
  say_fail "126 css=$css nope=$nope"
fi

echo "=== 127 port 5051, read-only 403, local address column ==="
cleanup_server
if start_server "$LOGDIR/http-5051.log" env PORT=5051; then
  echo "PASS 5051 started"
else
  say_fail "127 port 5051 did not start"
fi
code="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5051/ || true)"
echo "GET :5051/ -> $code"
if [[ "$code" == "200" ]]; then
  echo "PASS 127 GET 5051 200"
else
  say_fail "127 GET 5051 $code"
fi
cleanup_server
if start_server "$LOGDIR/http-ro.log" env HOTROOM_READONLY=1; then
  echo "PASS readonly started"
else
  say_fail "127 readonly did not start"
fi
ro="$(curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:5050/reset || true)"
echo "POST /reset -> $ro"
if [[ "$ro" == "403" ]]; then
  echo "PASS 127 readonly reset 403"
else
  say_fail "127 readonly reset $ro"
fi
echo "--- full ss line for local :5050, including the peer column ---"
ss -ltn | awk 'NR==1 || $4 ~ /:5050$/'
echo "--- local address column only ---"
locals="$(local_addrs_for 5050 || true)"
echo "local addresses: ${locals:-<none>}"
if [[ "$locals" == "127.0.0.1:5050" ]]; then
  echo "PASS 127 local address is 127.0.0.1:5050 and not 0.0.0.0:5050"
else
  say_fail "127 local address [${locals}]"
fi
if echo "$locals" | grep -q "0.0.0.0"; then
  say_fail "127 local column contains 0.0.0.0"
fi

cleanup_server
# The EXIT trap runs final_port_check even if a command above died under set -e.
echo "main checks done, fail=$fail"
exit "$fail"
