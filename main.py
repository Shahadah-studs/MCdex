from flask import Flask, request, render_template_string, escape
import base64
import io
import os
import traceback

from renderer import render_block_preview
from verifier import verify_block

# Modèle de code de bloc Minecraft officiel (Structure JSON)
MINECRAFT_BLOCK_TEMPLATE = """{{
    "format_version": "1.20.10",
    "minecraft:block": {{
        "description": {{
            "identifier": "shs_elite:{block_id}"
        }},
        "components": {{
            "minecraft:destructible_by_mining": {{
                "seconds_to_destroy": {destroy_time}
            }},
            "minecraft:light_emission": {light_level},
            "minecraft:friction": 0.6
        }}
    }}
}}"""

app = Flask(__name__)

# Small configuration override by environment
RETRY_LIMIT = int(os.environ.get("MCDEX_RETRY_LIMIT", "3"))
VERIFIER_TIMEOUT = int(os.environ.get("MCDEX_VERIFIER_TIMEOUT", "180"))  # seconds

FORM_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MCDex - Minecraft Block Generator</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        /* (kept compact) */
        body { background-color:#111; color:#00ff00; font-family:'Courier New', monospace; padding:20px; }
        .card{ background:#0f0f0f; padding:20px; border-radius:6px; border:1px solid #222; max-width:880px; margin:auto;}
        input[type=text]{ width:100%; padding:8px; background:#111; color:#fff; border:1px solid #333 }
        input[type=submit]{ background:#ffcc00; color:#111; padding:8px 12px; border:none; cursor:pointer }
        .layout { display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start; justify-content:center; }
        .left, .right { flex:1 1 420px; min-width:300px; }
        pre{ background:#1c1c1c; padding:15px; color:#fff; overflow:auto; }
        img.preview { border:1px solid #333; background:#000; max-width:320px; display:block; margin-bottom:10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>MCDex - Minecraft Block Generator</h2>
        <form method="post" action="/api/generate">
            <label>Block name: <input type="text" name="block_name" placeholder="elite_block" required></label>
            <label>Block type:
                <select name="block_type">
                    <option value="normal">Normal</option>
                    <option value="light">Light</option>
                    <option value="god_tier">God Tier</option>
                </select>
            </label>
            <input type="submit" value="Generate">
        </form>
    </div>
</body>
</html>
"""

RESULT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>MCDex - Result</title>
<style>
body { background:#111; color:#fff; font-family:monospace; padding:20px; }
.container { display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start; }
.left { flex:1 1 420px; min-width:300px; }
.right { width:360px; }
.preview { border:1px solid #333; background:#000; padding:8px; }
pre { background:#1c1c1c; padding:12px; overflow:auto; }
.status-pass { color:#7cff7c; font-weight:bold; }
.status-fail { color:#ff6b6b; font-weight:bold; }
</style>
</head>
<body>
    <div class="container">
        <div class="left">
            <div><strong>Generated block identifier:</strong> {{ block_id }}</div>
            <h3>Block JSON</h3>
            <pre>{{ generated_code }}</pre>
            <h3>Verification logs</h3>
            <pre>{{ verification_logs }}</pre>
            <div><a href="/">← Generate another block</a></div>
        </div>
        <div class="right">
            <div class="preview">
                <div><strong>Preview</strong></div>
                <img class="preview" src="data:image/png;base64,{{ preview_data }}" alt="block preview"/>
                <div>Status: <span class="{{ status_class }}">{{ status_text }}</span></div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return FORM_HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/api/generate", methods=["POST"])
def api_generate():
    # Wrap the whole handler to catch any exception and show it in the page (helps debug 500s)
    try:
        block_name = request.form.get('block_name', 'elite_block')
        block_type = request.form.get('block_type', 'normal')

        # sanitize
        block_id = (block_name or 'elite_block').lower().replace(' ', '_')
        for char in ['/', '\\', '"', "'", '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
            block_id = block_id.replace(char, '')

        if block_type == 'god_tier':
            destroy_time = 50.0
            light_level = 15
        elif block_type == 'light':
            destroy_time = 1.0
            light_level = 10
        else:
            destroy_time = 3.0
            light_level = 0

        generated_code = MINECRAFT_BLOCK_TEMPLATE.format(
            block_id=escape(block_id),
            destroy_time=destroy_time,
            light_level=light_level
        )

        final_success = False
        final_logs = ""
        preview_b64 = ""
        status_text = "UNKNOWN"
        status_class = ""

        # attempt verification with retries
        for attempt in range(1, RETRY_LIMIT + 1):
            # render preview
            img = render_block_preview(block_id, light_level=light_level, size=320)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            preview_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

            # try full verification
            ok, logs = verify_block(generated_code, block_id, timeout=VERIFIER_TIMEOUT)
            final_logs = f"Attempt {attempt}/{RETRY_LIMIT}\n" + (logs or '')
            if ok:
                final_success = True
                break
            # if not ok, loop again to retry (regeneration strategy could be improved by varying parameters)
        if final_success:
            status_text = "PASS (Fully verified on Java + Bedrock)"
            status_class = "status-pass"
        else:
            status_text = "FAIL (verification failed after retries)"
            status_class = "status-fail"

        html = render_template_string(
            RESULT_TEMPLATE,
            block_id=block_id,
            generated_code=generated_code,
            verification_logs=final_logs,
            preview_data=preview_b64,
            status_text=status_text,
            status_class=status_class
        )
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    except Exception:
        tb = traceback.format_exc()
        # Render a simple error page showing the traceback so you can debug the cause of 500
        error_html = render_template_string(
            """<!doctype html>
            <html>
            <head>
              <meta charset='utf-8'>
              <title>Error</title>
              <style>body { background:#111; color:#eee; font-family:monospace; padding:20px; }</style>
            </head>
            <body>
              <h1>Internal Server Error</h1>
              <pre>{{ tb }}</pre>
              <div><a href="/">← Back</a></div>
            </body>
            </html>
            """,
            tb=tb
        )
        return error_html, 500, {'Content-Type': 'text/html; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", "5000")))
