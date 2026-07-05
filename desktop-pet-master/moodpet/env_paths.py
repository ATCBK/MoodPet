from pathlib import Path
from typing import Optional


def resolve_env_path(base_dir: Path, filename: str = ".env") -> Optional[Path]:
    candidates = (
        base_dir / filename,
        base_dir.parent / filename,
        Path.cwd() / filename,
    )
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists():
            return candidate
    return None
