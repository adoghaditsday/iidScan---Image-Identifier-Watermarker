from pathlib import Path
from typing import Optional, Dict, Any

from .config import REPORT_DIR, APP_NAME, APP_VERSION
from .database import utc_now_iso


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:80]


def create_mark_report(record: Dict[str, Any], report_dir: Optional[Path] = None) -> Path:
    out_dir = Path(report_dir) if report_dir else REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    identifier = record.get("identifier_code", "unknown")
    path = out_dir / f"mark_report_{_safe_name(identifier)}.txt"

    text = f"""{APP_NAME} {APP_VERSION}
MARK REPORT

Status: New identifier embedded
Identifier: {record.get('identifier_code')}
Created At: {record.get('created_at')}
Original Filename: {record.get('original_filename')}
Original Path: {record.get('original_path')}
Marked Path: {record.get('marked_path')}
Snapshot Path: {record.get('snapshot_path')}
SHA-256 Original Hash: {record.get('sha256_hash')}

Signature Name: {record.get('signature_name') or ''}
Signature Note: {record.get('signature_note') or ''}

Report Generated At: {utc_now_iso()}
"""
    path.write_text(text, encoding="utf-8")
    return path


def create_scan_report(
    scanned_filename: str,
    scanned_path: str,
    extracted_payload: Optional[Dict[str, Any]],
    matched_record: Optional[Dict[str, Any]],
    signature_name: str = "",
    signature_note: str = "",
    report_dir: Optional[Path] = None,
) -> Path:
    out_dir = Path(report_dir) if report_dir else REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    identifier = extracted_payload.get("identifier_code") if extracted_payload else "NO_IDENTIFIER"
    path = out_dir / f"scan_report_{_safe_name(identifier)}_{_safe_name(scanned_filename)}.txt"

    if extracted_payload and matched_record:
        status = "Existing known identifier detected"
    elif extracted_payload:
        status = "Identifier detected, but no local database record was found"
    else:
        status = "No identifier detected"

    text = f"""{APP_NAME} {APP_VERSION}
SCAN REPORT

Status: {status}
Scanned Filename: {scanned_filename}
Scanned Path: {scanned_path}

Detected Identifier: {identifier}
Detected Payload Created At: {extracted_payload.get('created_at') if extracted_payload else ''}
Detected Payload Signature Name: {extracted_payload.get('signature_name') if extracted_payload else ''}
Detected Payload Signature Note: {extracted_payload.get('signature_note') if extracted_payload else ''}

Local Database Match: {'Yes' if matched_record else 'No'}
Original Filename: {matched_record.get('original_filename') if matched_record else ''}
Original Created At: {matched_record.get('created_at') if matched_record else ''}
Original Marked Path: {matched_record.get('marked_path') if matched_record else ''}
Original Snapshot Path: {matched_record.get('snapshot_path') if matched_record else ''}
Original Report Path: {matched_record.get('report_path') if matched_record else ''}

Scan Signature Name: {signature_name or ''}
Scan Signature Note: {signature_note or ''}

Report Generated At: {utc_now_iso()}
"""
    path.write_text(text, encoding="utf-8")
    return path
