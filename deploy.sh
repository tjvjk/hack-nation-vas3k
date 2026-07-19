#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
REMOTE_DIR="hack-nation-vas3k"

if [[ ! -f "${ENV_FILE}" ]]; then
	echo "Missing ${ENV_FILE}. Copy .env.example to .env and fill in its values." >&2
	exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

: "${SSH_HOST:?SSH_HOST must be set in .env}"
: "${SSH_KEY:?SSH_KEY must be set in .env}"

if [[ ! -f "${SSH_KEY}" ]]; then
	echo "SSH key does not exist: ${SSH_KEY}" >&2
	exit 1
fi

for command_name in ssh rsync; do
	if ! command -v "${command_name}" >/dev/null 2>&1; then
		echo "Required command is not installed: ${command_name}" >&2
		exit 1
	fi
done

REMOTE_HOST="${SSH_HOST}"
if [[ -n "${SSH_USER:-}" ]]; then
	REMOTE_HOST="${SSH_USER}@${SSH_HOST}"
fi

SSH_ARGS=(-i "${SSH_KEY}" -o IdentitiesOnly=yes)
printf -v SSH_KEY_QUOTED "%q" "${SSH_KEY}"
RSYNC_SSH="ssh -i ${SSH_KEY_QUOTED} -o IdentitiesOnly=yes"

echo "Preparing ${REMOTE_HOST}:~/${REMOTE_DIR}"
ssh "${SSH_ARGS[@]}" "${REMOTE_HOST}" "mkdir -p ~/${REMOTE_DIR}"

echo "Synchronizing project files"
rsync \
	--archive \
	--compress \
	--exclude=.git/ \
	--exclude=.venv/ \
	--exclude=.omx/ \
	--exclude=__pycache__/ \
	--exclude=.pytest_cache/ \
	--exclude=.ruff_cache/ \
	--exclude='*.db' \
	--exclude='*.db-shm' \
	--exclude='*.db-wal' \
	--rsh="${RSYNC_SSH}" \
	"${SCRIPT_DIR}/" \
	"${REMOTE_HOST}:~/${REMOTE_DIR}/"

echo "Building and starting Docker Compose services"
ssh "${SSH_ARGS[@]}" "${REMOTE_HOST}" \
	"cd ~/${REMOTE_DIR} && chmod 600 .env && docker compose up -d --build"

echo "Deployment completed"
