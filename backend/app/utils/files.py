"""File-safety helpers: safe filenames and path-traversal protection."""
import os
import re
import uuid


def safe_filename(original_name: str) -> str:
    """
    Generate a filesystem-safe, collision-proof filename while preserving the
    original extension. Strips any directory components to prevent path
    traversal via crafted filenames like '../../etc/passwd.pdf'.
    """
    base = os.path.basename(original_name)
    name, ext = os.path.splitext(base)
    ext = ext.lower() if ext.lower() == ".pdf" else ".pdf"
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:60]
    return f"{name}_{uuid.uuid4().hex[:12]}{ext}"


def resolve_within(base_dir: str, filename: str) -> str:
    """Resolve a filename inside base_dir, refusing to escape it."""
    base_dir = os.path.abspath(base_dir)
    full_path = os.path.abspath(os.path.join(base_dir, filename))
    if not full_path.startswith(base_dir + os.sep):
        raise ValueError("Invalid file path (path traversal attempt detected)")
    return full_path
