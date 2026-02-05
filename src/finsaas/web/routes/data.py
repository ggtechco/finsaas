"""CSV file upload and listing endpoints."""

from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

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


def _count_bars(path: Path) -> int:
    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            return sum(1 for _ in reader)
    except Exception:
        return 0
