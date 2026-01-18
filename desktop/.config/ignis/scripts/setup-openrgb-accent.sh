#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "error: this script must be run as root" >&2
  exit 1
fi

usage() {
  echo "usage: $0 <username> [--remove]" >&2
  exit 1
}

[[ $# -lt 1 || $# -gt 2 ]] && usage

USER_NAME="$1"
MODE="${2:-install}"

if ! id "${USER_NAME}" >/dev/null 2>&1; then
  echo "error: user '${USER_NAME}' does not exist" >&2
  exit 1
fi

if ! systemctl list-unit-files openrgb.service >/dev/null 2>&1; then
  echo "error: openrgb.service does not exist" >&2
  exit 1
fi

HOME_DIR="$(getent passwd "${USER_NAME}" | cut -d: -f6)"

OVERRIDE_DIR="/etc/systemd/system/openrgb.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/override.conf"

AFTER_SLEEP_SERVICE="/etc/systemd/system/openrgb-after-sleep.service"
BEFORE_SLEEP_SERVICE="/etc/systemd/system/openrgb-before-sleep.service"
BEFORE_SHUTDOWN_SERVICE="/etc/systemd/system/openrgb-before-shutdown.service"

SWITCH_COMMAND="/usr/local/bin/_openrgb-accent-update.sh"

if [[ "${MODE}" == "--remove" ]]; then
  systemctl disable --now openrgb-after-sleep.service 2>/dev/null || true
  systemctl disable --now openrgb-before-sleep.service 2>/dev/null || true
  systemctl disable --now openrgb-before-shutdown.service 2>/dev/null || true

  rm -f \
    "${OVERRIDE_FILE}" \
    "${AFTER_SLEEP_SERVICE}" \
    "${BEFORE_SLEEP_SERVICE}" \
    "${BEFORE_SHUTDOWN_SERVICE}" \
    "${SWITCH_COMMAND}"

  rmdir --ignore-fail-on-non-empty "${OVERRIDE_DIR}" 2>/dev/null || true

  systemctl daemon-reload
  exit 0
fi

mkdir -p "${OVERRIDE_DIR}"

cat > "${OVERRIDE_FILE}" <<EOF
[Service]
ExecStartPost=bash -c 'sleep 1 && ${SWITCH_COMMAND}'
ExecStop=${SWITCH_COMMAND} off
EOF

cat > "${AFTER_SLEEP_SERVICE}" <<EOF
[Unit]
Description=Apply OpenRGB preferred accent colour after resume
After=sleep.target openrgb.service
Requires=openrgb.service

[Service]
Type=oneshot
ExecStart=${SWITCH_COMMAND}

[Install]
WantedBy=sleep.target
# vim: ft=systemd
EOF

cat > "${BEFORE_SLEEP_SERVICE}" <<EOF
[Unit]
Description=Turn off OpenRGB lighting before suspend
Before=sleep.target
Requires=openrgb.service

[Service]
Type=oneshot
ExecStart=${SWITCH_COMMAND} off

[Install]
WantedBy=sleep.target
# vim: ft=systemd
EOF

cat > "${BEFORE_SHUTDOWN_SERVICE}" <<EOF
[Unit]
Description=Turn off OpenRGB lighting before shutdown
Before=shutdown.target reboot.target halt.target
Requires=openrgb.service

[Service]
Type=oneshot
ExecStart=${SWITCH_COMMAND} off

[Install]
WantedBy=halt.target reboot.target shutdown.target
# vim: ft=systemd
EOF

cat > "${SWITCH_COMMAND}" <<EOF
#!/usr/bin/env bash
set -euo pipefail

accent_file="${HOME_DIR}/.local/share/ignis/accent.txt"

if ! [ -f "\${accent_file}" ] || [[ "\${1:-}" == "off" ]]; then
  openrgb --mode direct --color 000000
  exit 0
fi
openrgb --mode direct --color \$(cat ${HOME_DIR}/.local/share/ignis/accent.txt)
EOF
chmod +x "${SWITCH_COMMAND}"

systemctl daemon-reload

systemctl enable openrgb.service
systemctl enable openrgb-after-sleep.service
systemctl enable openrgb-before-sleep.service
systemctl enable openrgb-before-shutdown.service

echo "Set /usr/local/bin/_openrgb-accent-update.sh as your post accent colour change command in the settings"
