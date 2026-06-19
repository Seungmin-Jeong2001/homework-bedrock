#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/lambda"
ZIP_PATH="${ROOT_DIR}/build/lambda.zip"
rm -rf "${BUILD_DIR}" "${ZIP_PATH}"
mkdir -p "${BUILD_DIR}"

if python3 -m pip --version >/dev/null 2>&1; then
  python3 -m pip install -r "${ROOT_DIR}/lambda/requirements.txt" -t "${BUILD_DIR}"
else
  echo "python3 -m pip is not available; packaging source only."
  echo "AWS Lambda Python runtimes include boto3, which is the only listed dependency."
fi
cp "${ROOT_DIR}/lambda/orchestrator.py" "${BUILD_DIR}/orchestrator.py"

(
  cd "${BUILD_DIR}"
  zip -qr "${ZIP_PATH}" .
)

echo "Created ${ZIP_PATH}"
