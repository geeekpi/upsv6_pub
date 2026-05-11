#!/usr/bin/env bash
set -euo pipefail

START_SERVICE=0
if [[ "${1:-}" == "--start" ]]; then
  START_SERVICE=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--start]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

sudo apt-get update
sudo apt-get install -y python3 python3-pip i2c-tools

if apt-cache show python3-smbus2 >/dev/null 2>&1; then
  sudo apt-get install -y python3-smbus2
else
  sudo pip3 install smbus2
fi

sudo install -o root -g root -m 0755 \
  "${REPO_ROOT}/scripts/ups_power_guard.py" \
  /usr/local/sbin/ups_power_guard.py

sudo install -o root -g root -m 0644 \
  "${REPO_ROOT}/systemd/ups-power-guard.service" \
  /etc/systemd/system/ups-power-guard.service

if [[ ! -f /etc/default/ups-power-guard ]]; then
  sudo tee /etc/default/ups-power-guard >/dev/null <<'EOF'
# UPS Power Guard configuration for 52Pi / GeekPi UPS V6
#
# Native InfluxDB systemd service example:
# UPS_STOP_COMMANDS='[["systemctl","stop","influxdb"]]'
# UPS_START_COMMANDS='[["systemctl","start","influxdb"]]'
#
# Docker container example:
# UPS_STOP_COMMANDS='[["docker","stop","-t","60","influxdb3-core"],["docker","stop","-t","30","grafana"]]'
# UPS_START_COMMANDS='[["docker","start","influxdb3-core"],["docker","start","grafana"]]'
#
# Docker Compose stack example:
# UPS_STOP_COMMANDS='[["docker","compose","-f","/opt/upsv6_pub/deploy/docker-compose.yml","stop","influxdb3-core","grafana"]]'
# UPS_START_COMMANDS='[["docker","compose","-f","/opt/upsv6_pub/deploy/docker-compose.yml","up","-d","influxdb3-core","grafana"]]'
#
# Recommended initial thresholds:
# UPS_INPUT_PRESENT_MV=4500
# UPS_POWER_LOSS_DEBOUNCE_SEC=8
# UPS_BATTERY_SHUTDOWN_MV=7600
# UPS_MAX_OUTAGE_RUNTIME_SEC=180
# UPS_POLL_SEC=2
EOF
fi

sudo systemctl daemon-reload
sudo systemctl enable ups-power-guard.service

if [[ "${START_SERVICE}" -eq 1 ]]; then
  sudo systemctl start ups-power-guard.service
fi

echo "Installed UPS power guard."
echo
echo "Status:"
echo "  sudo systemctl status ups-power-guard.service"
echo
echo "Logs:"
echo "  sudo journalctl -u ups-power-guard.service -f"
echo
if [[ "${START_SERVICE}" -eq 0 ]]; then
  echo "Start service manually when ready:"
  echo "  sudo systemctl start ups-power-guard.service"
fi
