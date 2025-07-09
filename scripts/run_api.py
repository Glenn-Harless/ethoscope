import sys
from pathlib import Path

import uvicorn

sys.path.append(str(Path(__file__).parent.parent))

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
