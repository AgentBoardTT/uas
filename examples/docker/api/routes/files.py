"""File management endpoints."""

import io
import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..models import FileInfo, UploadResponse
from ..session_manager import SessionNotFoundError, session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["files"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def get_workspace_path(session_id: str, container_info: dict) -> Path:
    """Get the workspace path for a session."""
    # For subprocess provider, use the workspace_dir
    if container_info.get("provider") == "subprocess":
        return Path(container_info.get("workspace_dir", "/tmp"))

    # For Docker, we need to access the volume
    # This is a simplified version - in production, you'd use Docker API
    return Path(f"/tmp/uas-workspaces/{container_info.get('agent_id', session_id)}")


@router.get("/{session_id}/list", response_model=list[FileInfo])
async def list_files(session_id: str, path: str = ""):
    """List files in the workspace."""
    try:
        session = await session_manager.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    workspace = get_workspace_path(session_id, session.container_info)
    target_path = workspace / path

    if not target_path.exists():
        return []

    files = []
    try:
        for entry in target_path.iterdir():
            stat = entry.stat()
            files.append(FileInfo(
                name=entry.name,
                path=str(entry.relative_to(workspace)),
                size=stat.st_size if entry.is_file() else 0,
                is_directory=entry.is_dir(),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            ))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return sorted(files, key=lambda f: (not f.is_directory, f.name.lower()))


@router.post("/{session_id}/upload", response_model=UploadResponse)
async def upload_files(
    session_id: str,
    files: list[UploadFile] = File(...),
    path: str = "",
):
    """Upload files to the workspace."""
    try:
        session = await session_manager.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    workspace = get_workspace_path(session_id, session.container_info)
    target_dir = workspace / path
    target_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    failed = []

    for file in files:
        try:
            # Check file size
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                failed.append(f"{file.filename}: File too large")
                continue

            # Save file
            file_path = target_dir / file.filename
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded.append(file.filename)
            logger.info(f"Uploaded {file.filename} to {session_id}")

        except Exception as e:
            failed.append(f"{file.filename}: {str(e)}")

    return UploadResponse(uploaded_files=uploaded, failed_files=failed)


@router.get("/{session_id}/download")
async def download_workspace(session_id: str):
    """Download the entire workspace as a ZIP file."""
    try:
        session = await session_manager.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    workspace = get_workspace_path(session_id, session.container_info)

    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Create ZIP in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(workspace):
            for file in files:
                file_path = Path(root) / file
                arc_name = file_path.relative_to(workspace)
                zf.write(file_path, arc_name)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="workspace-{session_id}.zip"'
        },
    )


@router.get("/{session_id}/read")
async def read_file(session_id: str, path: str):
    """Read a file from the workspace."""
    try:
        session = await session_manager.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")

    workspace = get_workspace_path(session_id, session.container_info)
    file_path = workspace / path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    try:
        with open(file_path, "r") as f:
            content = f.read()
        return {"path": path, "content": content}
    except UnicodeDecodeError:
        # Binary file - return base64
        import base64
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        return {"path": path, "content": content, "encoding": "base64"}
