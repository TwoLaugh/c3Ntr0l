from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg != "--check"]
    check = "--check" in sys.argv[1:]
    output_path = Path(args[0] if args else "openapi.json")
    content = json.dumps(app.openapi(), indent=2) + "\n"

    if check:
        if not output_path.exists():
            print(f"OpenAPI spec does not exist: {output_path}", file=sys.stderr)
            return 1
        existing = output_path.read_text(encoding="utf-8")
        if existing != content:
            print(f"OpenAPI spec is stale: {output_path}", file=sys.stderr)
            return 1
        print(f"OpenAPI spec is current: {output_path}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote OpenAPI spec to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
