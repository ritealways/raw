"""
run_integration.py

Runs the full cycle against your real Anaplan production tenant:
discover -> export -> forecast -> import.

Usage:
    python run_integration.py \
        --email you@company.com --password *** \
        --workspace-id <ws> --model-id <model> \
        --export-id <exportId> --export-file-id <fileId> \
        --import-id <importId> --import-file-id <fileId>

Credentials should come from environment variables or a secrets manager in
any real deployment -- the --password flag here is for local testing only.
"""

import argparse
import logging
import sys

from anaplan_client import AnaplanClient, AnaplanAPIError
from forecast_engine import run_forecast

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_integration")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--workspace-id", required=True)
    p.add_argument("--model-id", required=True)
    p.add_argument("--export-id", required=True)
    p.add_argument("--export-file-id", required=True)
    p.add_argument("--import-id", required=True)
    p.add_argument("--import-file-id", required=True)
    p.add_argument("--periods-ahead", type=int, default=3)
    args = p.parse_args()

    client = AnaplanClient()  # defaults to https://api.anaplan.com/2/0
    client.authenticate_basic(args.email, args.password)
    log.info("Authenticated")

    try:
        log.info("Running export %s ...", args.export_id)
        export_df = client.export_view_to_dataframe(
            args.workspace_id, args.model_id, args.export_id, args.export_file_id
        )
        log.info("Exported %d rows", len(export_df))

        log.info("Running forecast ...")
        forecast_df = run_forecast(export_df, periods_ahead=args.periods_ahead)
        log.info("Forecast produced %d rows", len(forecast_df))

        log.info("Uploading forecast and running import %s ...", args.import_id)
        client.upload_dataframe(
            args.workspace_id, args.model_id, args.import_file_id,
            forecast_df, file_name="forecast_writeback.csv",
        )
        task = client.run_import(args.workspace_id, args.model_id, args.import_id)
        log.info("Import complete: %s", task.get("result", {}))

    except AnaplanAPIError as exc:
        log.error("Integration failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
