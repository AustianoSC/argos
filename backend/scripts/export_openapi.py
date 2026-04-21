"""Export the OpenAPI spec to a JSON file without running the server."""

import json
from pathlib import Path

from argos.api.app import app

spec = app.openapi()
output = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "api" / "openapi.json"
output.write_text(json.dumps(spec, indent=2))
print(f"Exported OpenAPI spec to {output}")
