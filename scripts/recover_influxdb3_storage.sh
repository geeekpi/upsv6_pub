#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="influxdb3-core"
DATA_PATH="/var/lib/influxdb3"
HELPER_IMAGE="alpine:3.20"
DRY_RUN=0
ASSUME_YES=0
RESTART_IF_STOPPED_BY_SCRIPT=1

usage() {
  cat <<'EOF'
Usage: recover_influxdb3_storage.sh [options]

Remove zero-byte InfluxDB 3 `.catalog` and `.wal` files, plus the newest `.wal`
file, from a Docker-backed InfluxDB 3 data directory.

Options:
  --container NAME     Docker container name (default: influxdb3-core)
  --data-path PATH     In-container InfluxDB data path (default: /var/lib/influxdb3)
  --helper-image IMG   Helper image used to access the mounted data (default: alpine:3.20)
  --dry-run            Print what would be removed without changing anything
  --yes                Skip the interactive confirmation prompt
  --no-restart         Leave the container stopped after cleanup
  -h, --help           Show this help

Examples:
  sudo ./scripts/recover_influxdb3_storage.sh --dry-run
  sudo ./scripts/recover_influxdb3_storage.sh --yes
EOF
}

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --container)
      CONTAINER_NAME="${2:-}"
      shift 2
      ;;
    --data-path)
      DATA_PATH="${2:-}"
      shift 2
      ;;
    --helper-image)
      HELPER_IMAGE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --yes)
      ASSUME_YES=1
      shift
      ;;
    --no-restart)
      RESTART_IF_STOPPED_BY_SCRIPT=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

command -v docker >/dev/null 2>&1 || die "docker is required"

docker inspect "${CONTAINER_NAME}" >/dev/null || die "Failed to inspect container '${CONTAINER_NAME}'"

container_running="$(
  docker inspect --format '{{if .State.Running}}true{{else}}false{{end}}' "${CONTAINER_NAME}"
)"

mount_source="$(
  docker inspect \
    --format '{{range .Mounts}}{{if eq .Destination "'"${DATA_PATH}"'"}}{{.Source}}{{end}}{{end}}' \
    "${CONTAINER_NAME}"
)"

if [[ -z "${mount_source}" ]]; then
  die "No Docker mount found for data path '${DATA_PATH}' in container '${CONTAINER_NAME}'"
fi

helper_target="/recovery"

find_zero_byte_command=(
  find "${helper_target}" -type f '(' -name '*.catalog' -o -name '*.wal' ')' -size 0 -print
)

newest_wal_command=(
  sh -c "find '${helper_target}' -type f -name '*.wal' | sort | tail -n 1"
)

run_helper() {
  docker run --rm -v "${mount_source}:${helper_target}" "${HELPER_IMAGE}" "$@"
}

mapfile -t zero_byte_matches < <(run_helper "${find_zero_byte_command[@]}")
latest_wal="$(run_helper "${newest_wal_command[@]}" | tr -d '\r')"

declare -A removal_map=()

for path in "${zero_byte_matches[@]}"; do
  [[ -n "${path}" ]] || continue
  removal_map["${path}"]=1
done

if [[ -n "${latest_wal}" ]]; then
  removal_map["${latest_wal}"]=1
fi

if [[ ${#removal_map[@]} -eq 0 ]]; then
  log "No zero-byte .catalog/.wal files or latest .wal file found under ${DATA_PATH}"
  exit 0
fi

mapfile -t removal_list < <(printf '%s\n' "${!removal_map[@]}" | sort)

log "Container: ${CONTAINER_NAME}"
log "Data path: ${DATA_PATH}"
log "Mount source: ${mount_source}"
log "Files selected for removal:"
for path in "${removal_list[@]}"; do
  log "  ${path}"
done

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "Dry run enabled; no files were removed"
  exit 0
fi

if [[ "${ASSUME_YES}" -ne 1 ]]; then
  printf 'Proceed with deletion and optional container restart? [y/N] '
  read -r reply
  if [[ ! "${reply}" =~ ^[Yy]$ ]]; then
    log "Aborted"
    exit 0
  fi
fi

stopped_by_script=0
if [[ "${container_running}" == "true" ]]; then
  log "Stopping container ${CONTAINER_NAME}"
  docker stop -t 60 "${CONTAINER_NAME}" >/dev/null
  stopped_by_script=1
else
  log "Container ${CONTAINER_NAME} is already stopped"
fi

cleanup() {
  if [[ "${stopped_by_script}" -eq 1 && "${RESTART_IF_STOPPED_BY_SCRIPT}" -eq 1 ]]; then
    log "Restarting container ${CONTAINER_NAME}"
    docker start "${CONTAINER_NAME}" >/dev/null
  fi
}

trap cleanup EXIT

log "Removing selected files"
run_helper rm -f -- "${removal_list[@]}" >/dev/null
log "Removed ${#removal_list[@]} file(s)"
