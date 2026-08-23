"""
anaplan_client.py

Wrapper around the Anaplan Integration API v2 (Bulk API), for a real
Anaplan production tenant only   https://api.anaplan.com/2/0.

Every call in this file is a real HTTP request against your live Anaplan
account. There is no mock or offline mode.

Reference: https://help.anaplan.com/integration-api-v20-3107aa54-d12b-4c48-9550-3561c84adbb2
"""

from __future__ import annotations
import base64
import time
import logging
from dataclasses import dataclass
from typing import Optional, Iterator

import requests

logger = logging.getLogger("anaplan_client")

PRODUCTION_BASE_URL = "https://api.anaplan.com/2/0"
AUTH_URL = "https://auth.anaplan.com/token/authenticate"
AUTH_REFRESH_URL = "https://auth.anaplan.com/token/refresh"
TOKEN_LIFETIME_S = 35 * 60          # Anaplan tokens are valid for 35 minutes
REFRESH_MARGIN_S = 5 * 60           # refresh 5 minutes before expiry
CHUNK_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB; Anaplan accepts 1-50 MB per chunk
MAX_RETRIES = 5
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class AnaplanAPIError(RuntimeError):
    """Raised when Anaplan returns a non-retryable error or a task fails."""


@dataclass
class AnaplanAuth:
    token: str
    obtained_at: float

    @property
    def expires_at(self) -> float:
        return self.obtained_at + TOKEN_LIFETIME_S

    @property
    def needs_refresh(self) -> bool:
        return time.time() > (self.expires_at - REFRESH_MARGIN_S)

    @property
    def header(self) -> dict:
        return {"Authorization": f"AnaplanAuthToken {self.token}"}


class AnaplanClient:
    def __init__(self, base_url: str = PRODUCTION_BASE_URL):
        """base_url defaults to the production Anaplan API root."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._auth: Optional[AnaplanAuth] = None

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def authenticate_basic(self, email: str, password: str) -> AnaplanAuth:
        """POST to the Auth Service with HTTP Basic credentials. Returns a
        token valid for 35 minutes. Anaplan explicitly recommends reusing
        one token for the whole session rather than re-authenticating per
        call   repeated re-auth can itself trigger request failures."""
        creds = base64.b64encode(f"{email}:{password}".encode()).decode()
        resp = requests.post(AUTH_URL, headers={"Authorization": f"Basic {creds}"})
        resp.raise_for_status()
        token = resp.json()["tokenInfo"]["tokenValue"]
        self._auth = AnaplanAuth(token=token, obtained_at=time.time())
        self.session.headers.update(self._auth.header)
        return self._auth

    def authenticate_certificate(self, encoded_cert: str, encoded_signed_data: str) -> AnaplanAuth:
        """CA-certificate auth   the recommended approach for an unattended
        service account (no password rotation, no 90-day expiry). Requires
        a CA certificate uploaded in Anaplan Administration > Security, and
        the corresponding private key used to sign the auth payload
        (encoded_signed_data) before calling this method."""
        resp = requests.post(
            AUTH_URL,
            headers={"Authorization": f"CACertificate {encoded_cert}"},
            json={"encodedData": encoded_cert, "encodedSignedData": encoded_signed_data},
        )
        resp.raise_for_status()
        token = resp.json()["tokenInfo"]["tokenValue"]
        self._auth = AnaplanAuth(token=token, obtained_at=time.time())
        self.session.headers.update(self._auth.header)
        return self._auth

    def refresh_if_needed(self) -> None:
        """Anaplan tokens expire after 35 minutes. Call this before any
        request in a long-running job; it refreshes only when close to
        expiry rather than on every call."""
        if self._auth is None:
            raise AnaplanAPIError("Not authenticated   call authenticate_basic/"
                                   "authenticate_certificate first.")
        if not self._auth.needs_refresh:
            return
        resp = requests.post(AUTH_REFRESH_URL, headers=self._auth.header)
        resp.raise_for_status()
        token = resp.json()["tokenInfo"]["tokenValue"]
        self._auth = AnaplanAuth(token=token, obtained_at=time.time())
        self.session.headers.update(self._auth.header)
        logger.info("Auth token refreshed")

    # ------------------------------------------------------------------ #
    # Low-level request wrapper with retry on transient failures
    # ------------------------------------------------------------------ #
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        self.refresh_if_needed()
        url = f"{self.base_url}{path}"
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(method, url, **kwargs)
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt, 30))
                continue
            if resp.status_code in RETRYABLE_STATUS:
                wait = min(2 ** attempt, 30)
                logger.warning("HTTP %s on %s %s   retrying in %ss (attempt %s/%s)",
                                resp.status_code, method, path, wait, attempt, MAX_RETRIES)
                time.sleep(wait)
                continue
            if not resp.ok:
                raise AnaplanAPIError(f"{method} {path} failed: {resp.status_code} {resp.text[:500]}")
            return resp
        raise AnaplanAPIError(f"{method} {path} failed after {MAX_RETRIES} retries: {last_exc}")

    # ------------------------------------------------------------------ #
    # Discovery
    # ------------------------------------------------------------------ #
    def list_workspaces(self) -> list:
        return self._request("GET", "/workspaces").json()["workspaces"]

    def list_models(self, workspace_id: str) -> list:
        return self._request("GET", f"/workspaces/{workspace_id}/models").json()["models"]

    def _list_model_resource(self, workspace_id: str, model_id: str, resource: str) -> list:
        return self._request(
            "GET", f"/workspaces/{workspace_id}/models/{model_id}/{resource}"
        ).json()[resource]

    def list_modules(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "modules")

    def list_views(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "views")

    def list_lists(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "lists")

    def list_files(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "files")

    def list_imports(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "imports")

    def list_exports(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "exports")

    def list_processes(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "processes")

    def list_actions(self, ws: str, model: str) -> list:
        return self._list_model_resource(ws, model, "actions")

    # ------------------------------------------------------------------ #
    # Task lifecycle shared by exports, imports, processes, actions
    # ------------------------------------------------------------------ #
    def _start_task(self, ws: str, model: str, resource: str, resource_id: str) -> str:
        resp = self._request(
            "POST",
            f"/workspaces/{ws}/models/{model}/{resource}/{resource_id}/tasks",
            json={"localeName": "en_US"},
        )
        return resp.json()["task"]["taskId"]

    def _poll_task(self, ws: str, model: str, resource: str, resource_id: str,
                    task_id: str, poll_interval_s: float = 2.0, timeout_s: float = 900.0) -> dict:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            resp = self._request(
                "GET",
                f"/workspaces/{ws}/models/{model}/{resource}/{resource_id}/tasks/{task_id}",
            )
            task = resp.json()["task"]
            state = task["taskState"]
            if state == "COMPLETE":
                result = task.get("result", {})
                if not result.get("successful", True):
                    raise AnaplanAPIError(
                        f"{resource[:-1]} task {task_id} completed with failures: {result}"
                    )
                return task
            if state == "FAILED":
                raise AnaplanAPIError(f"{resource[:-1]} task {task_id} failed: {task}")
            time.sleep(poll_interval_s)
        raise AnaplanAPIError(f"{resource[:-1]} task {task_id} did not complete within {timeout_s}s")

    # ------------------------------------------------------------------ #
    # Export: Anaplan -> us
    # ------------------------------------------------------------------ #
    def run_export(self, ws: str, model: str, export_id: str) -> dict:
        """Runs an export action end-to-end and returns the completed task."""
        task_id = self._start_task(ws, model, "exports", export_id)
        return self._poll_task(ws, model, "exports", export_id, task_id)

    def download_file(self, ws: str, model: str, file_id: str) -> bytes:
        """Downloads every chunk of a file (export output) and concatenates
        them in order. Anaplan serves export output as chunked
        application/octet-stream regardless of the source file's text
        format, so chunks are joined as raw bytes, then decoded once."""
        chunks_meta = self._request(
            "GET", f"/workspaces/{ws}/models/{model}/files/{file_id}/chunks"
        ).json()
        chunk_ids = [c["id"] for c in chunks_meta.get("chunks", [])]
        data = b""
        for chunk_id in chunk_ids:
            resp = self._request(
                "GET",
                f"/workspaces/{ws}/models/{model}/files/{file_id}/chunks/{chunk_id}",
                headers={"Accept": "application/octet-stream"},
            )
            data += resp.content
        return data

    def export_view_to_dataframe(self, ws: str, model: str, export_id: str, file_id: str):
        """Convenience: run export, download, parse as CSV -> pandas DataFrame."""
        import pandas as pd
        from io import BytesIO

        self.run_export(ws, model, export_id)
        raw = self.download_file(ws, model, file_id)
        return pd.read_csv(BytesIO(raw))

    # ------------------------------------------------------------------ #
    # Import: us -> Anaplan
    # ------------------------------------------------------------------ #
    def _chunk_bytes(self, data: bytes, chunk_size: int = CHUNK_SIZE_BYTES) -> Iterator[bytes]:
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def upload_file(self, ws: str, model: str, file_id: str, data: bytes,
                     file_name: str, header_row: int = 1, first_data_row: int = 2) -> None:
        """Full upload sequence per Anaplan's documented pattern:
        1. Set chunk count to -1 (tells Anaplan not to expect a fixed count
           up front; we mark completion explicitly at the end instead).
        2. PUT each chunk in order, 1-50 MB each.
        3. POST .../complete with the real chunk count once all chunks land.
        """
        self._request(
            "POST", f"/workspaces/{ws}/models/{model}/files/{file_id}",
            json={"chunkCount": -1},
        )

        chunk_count = 0
        for chunk_id, chunk in enumerate(self._chunk_bytes(data)):
            self._request(
                "PUT",
                f"/workspaces/{ws}/models/{model}/files/{file_id}/chunks/{chunk_id}",
                data=chunk,
                headers={"Content-Type": "application/octet-stream"},
            )
            chunk_count += 1
            logger.info("Uploaded chunk %s (%d bytes)", chunk_id, len(chunk))

        self._request(
            "POST", f"/workspaces/{ws}/models/{model}/files/{file_id}/complete",
            json={
                "id": file_id,
                "name": file_name,
                "chunkCount": chunk_count,
                "headerRow": header_row,
                "firstDataRow": first_data_row,
            },
        )

    def upload_dataframe(self, ws: str, model: str, file_id: str, df, file_name: str) -> None:
        """Convenience: pandas DataFrame -> CSV bytes -> upload_file()."""
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        self.upload_file(ws, model, file_id, csv_bytes, file_name)

    def run_import(self, ws: str, model: str, import_id: str) -> dict:
        """Runs the import action against the file already uploaded via
        upload_file(). Returns the completed task, including per-row
        failure counts if the import partially failed."""
        task_id = self._start_task(ws, model, "imports", import_id)
        task = self._poll_task(ws, model, "imports", import_id, task_id)
        result = task.get("result", {})
        if result.get("failureDumpAvailable"):
            logger.warning(
                "Import %s completed with row-level failures   "
                "call get_import_failure_dump() to inspect them.", import_id
            )
        return task

    def get_import_failure_dump(self, ws: str, model: str, import_id: str, task_id: str) -> bytes:
        """Downloads the dump file listing rows that failed validation
        during an import, when the task result reports one is available."""
        resp = self._request(
            "GET",
            f"/workspaces/{ws}/models/{model}/imports/{import_id}/tasks/{task_id}/dump",
            headers={"Accept": "application/octet-stream"},
        )
        return resp.content

    # ------------------------------------------------------------------ #
    # Processes and actions (e.g. chaining export -> import server-side,
    # or clearing a module before writeback)
    # ------------------------------------------------------------------ #
    def run_process(self, ws: str, model: str, process_id: str) -> dict:
        task_id = self._start_task(ws, model, "processes", process_id)
        return self._poll_task(ws, model, "processes", process_id, task_id)

    def run_action(self, ws: str, model: str, action_id: str) -> dict:
        task_id = self._start_task(ws, model, "actions", action_id)
        return self._poll_task(ws, model, "actions", action_id, task_id)
