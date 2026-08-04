from flask import Flask, request, render_template_string, escape

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

FORM_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SHS ELITE AI - Minecraft Block Generator</title>
    <style>
        body { background-color: #111; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
        .card { background: #0f0f0f; padding: 20px; border-radius: 6px; border: 1px solid #222; max-width: 800px; }
        label, select, input { display:block; margin-bottom:10px; }
        input[type=text] { width:100%; padding:8px; background:#111; color:#fff; border:1px solid #333 }
        input[type=submit] { background:#ffcc00; color:#111; padding:8px 12px; border:none; cursor:pointer }
    </style>
</head>
<body>
    <div class="card">
        <h2>SHS ELITE AI - Minecraft Block Generator</h2>
        <form method="post">
            <label>Block name: <input type="text" name="block_name" placeholder="elite_block"></label>
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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Read form values
        block_name = request.form.get('block_name', 'elite_block')
        block_type = request.form.get('block_type', 'normal')

        # Clean up name for Minecraft identifier
        block_id = (block_name or 'elite_block').lower().replace(' ', '_')
        for char in ['/', '\\', '"', "'", '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
            block_id = block_id.replace(char, '')

        # Tier logic
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

        html_response = render_template_string("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { background-color: #111; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
        pre { background-color: #1c1c1c; padding: 15px; border: 1px solid #333; overflow-x: auto; color: #fff; white-space: pre-wrap; word-wrap: break-word; }
        .title { color: #ffcc00; font-weight: bold; margin-bottom: 10px; font-size: 16px; letter-spacing: 1px; }
        a { color: #ffcc00; }
    </style>
</head>
<body>
    <div class="title">⚡ SHS ELITE AI - MINECRAFT CODE SUCCESSFUL:</div>
    <p>Copy this into your Behavior Pack (components/blocks/{{ block_id }}.json):</p>
    <pre>{{ generated_code }}</pre>
    <br>
    <a href="/">[ ← GENERATE ANOTHER BLOCK ]</a>
</body>
</html>
""", block_id=block_id, generated_code=generated_code)

        return html_response, 200, {'Content-Type': 'text/html; charset=utf-8'}

    # GET -> show form
    return FORM_HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
