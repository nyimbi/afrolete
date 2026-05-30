#!/bin/sh
set -eu

mkdir -p \
  "${AFROLETE_REPORT_ARTIFACT_DIR:-data/report-artifacts}" \
  "${AFROLETE_EQUIPMENT_FILE_DIR:-data/equipment-files}" \
  "${AFROLETE_TRAVEL_RECEIPT_FILE_DIR:-data/travel-receipts}" \
  "${AFROLETE_TRAVEL_CHECKLIST_FILE_DIR:-data/travel-checklist-files}" \
  "${AFROLETE_TRAVEL_MANIFEST_FILE_DIR:-data/travel-manifests}" \
  "${AFROLETE_SAFEGUARDING_INCIDENT_ARTIFACT_DIR:-data/safeguarding-incident-artifacts}" \
  "${AFROLETE_PERFORMANCE_HIGHLIGHT_EXPORT_DIR:-data/performance-highlight-exports}"

if [ "${AFROLETE_RUN_MIGRATIONS:-1}" = "1" ]; then
  alembic upgrade head
fi

if [ "${AFROLETE_SEED_DEMO:-0}" = "1" ]; then
  python -m app.demo_seed
fi

exec "$@"
