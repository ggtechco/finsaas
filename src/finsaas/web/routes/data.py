"""CSV file upload, listing, and preview endpoints."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, UploadFile

from finsaas.web import UPLOAD_DIR
from finsaas.web.schemas import FileInfo

router = APIRouter(tags=["data"])


@router.post("/data/upload")
async def upload_csv(file: UploadFile) -> FileInfo:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    dest = UPLOAD_DIR / file.filename
    content = await file.read()
    dest.write_bytes(content)

    bar_count = _count_bars(dest)
    return FileInfo(name=file.filename, size=len(content), bars=bar_count)


@router.get("/data/files")
def list_files() -> list[FileInfo]:
    if not UPLOAD_DIR.exists():
        return []
    files: list[FileInfo] = []
    for p in sorted(UPLOAD_DIR.glob("*.csv")):
        files.append(FileInfo(name=p.name, size=p.stat().st_size, bars=_count_bars(p)))
    return files


@router.get("/data/preview/{filename}")
def preview_csv(filename: str, rows: int = Query(default=10, ge=1, le=100)) -> Dict[str, Any]:
    """Return headers + first N rows + total bar count for a CSV file."""
    path = UPLOAD_DIR / filename
    if not path.exists() or not path.name.endswith(".csv"):
        raise HTTPException(status_code=404, detail="File not found")

    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            data_rows: List[List[str]] = []
            total = 0
            for row in reader:
                total += 1
                if len(data_rows) < rows:
                    data_rows.append(row)
        return {
            "filename": filename,
            "headers": headers,
            "rows": data_rows,
            "total_bars": total,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _count_bars(path: Path) -> int:
    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            return sum(1 for _ in reader)
    except Exception:
        return 0
