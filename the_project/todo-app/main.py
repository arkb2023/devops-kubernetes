from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uuid
import hashlib
import os

app = FastAPI()
port = os.environ.get("PORT", "3000")
print(f"Starting app on port {port}...")
app_mode = os.environ.get("APP_MODE", "Production")
print(f"App mode: {app_mode}")
app_hash = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:8]
print(f"Application hash: {app_hash}")
@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    req_hash = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:8]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Exercise 1.8 Output</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
      background-color: #f8f9fa;
      color: #333;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    h2 {{
      margin-bottom: 10px;
      color: #2c3e50;
    }}
    .hash {{
      font-family: monospace;
      background: #e1e1e1;
      padding: 4px 8px;
      border-radius: 4px;
      display: inline-block;
      margin-top: 6px;
    }}
    .label {{
      font-weight: bold;
      margin-right: 4px;
    }}
    .note {{
      margin-top: 20px;
      font-style: italic;
      color: #666;
    }}

  </style>
</head>
<body>
  <h2>Exercise: 1.8. The project, step 5</h2>

  <div><span class="label">Application Hash:</span><span class="hash">{app_hash}</span></div>
  <div><span class="label">Request Hash:</span><span class="hash">{req_hash}</span></div>

  <div class="note">Refresh the page to see a new request hash.</div>
</body>
</html>"""

    return HTMLResponse(content=html)
