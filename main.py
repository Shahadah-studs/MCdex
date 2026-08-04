import os
from flask import Flask, request, make_response

app = Flask(__name__)

# Modèle de code Minecraft débogué (les doubles accolades protègent la structure JSON)
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

@app.route('/generate-mod', methods=['POST'])
def generate_mod():
    # 1. Récupération sécurisée des données du formulaire HTML
    block_name = request.form.get('block_name', 'elite_block')
    block_type = request.form.get('block_type', 'normal')
    
    # 2. Nettoyage de l'identifiant pour éviter de casser les fichiers Minecraft
    block_id = block_name.lower().replace(" ", "_")
    for char in ['/', '\\', '"', "'", '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
        block_id = block_id.replace(char, "")
    
    # 3. Logique des paliers (Tiers) de blocs
    if block_type == "god_tier":
        destroy_time = 50.0
        light_level = 15
    elif block_type == "light":
        destroy_time = 1.0
        light_level = 10
    else:
        destroy_time = 3.0
        light_level = 0
        
    # 4. Injection sécurisée des variables dans le template
    generated_code = MINECRAFT_BLOCK_TEMPLATE.format(
        block_id=block_id,
        destroy_time=destroy_time,
        light_level=light_level
    )
    
    # 5. Construction de la page HTML de réponse pour l'iframe
    html_response = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background-color: #111; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }}
            pre {{ background-color: #1c1c1c; padding: 15px; border: 1px solid #333; overflow-x: auto; color: #fff; white-space: pre-wrap; word-wrap: break-word; }}
            .title {{ color: #ffcc00; font-weight: bold; margin-bottom: 10px; font-size: 16px; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="title">⚡ SHS ELITE AI GENERATOR - CODE SUCCESSFUL:</div>
        <p>Copy this code into your Minecraft Behavior Pack (components/blocks/{block_id}.json):</p>
        <pre>{generated_code}</pre>
        <br>
        <a href="javascript:history.back()" style="color: #ffcc00; text-decoration: none; font-weight: bold;">[ ← GENERATE ANOTHER BLOCK ]</a>
    </body>
    </html>
    """
    
    # 6. Activation de la sécurité CORS pour autoriser l'affichage dans l'iframe Vercel
    response = make_response(html_response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

if __name__ == '__main__':
    # Configuration dynamique du port requise par les serveurs gratuits de Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

    # 6. Activation de la sécurité CORS et suppression du blocage d'iframe
    response = make_response(html_response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    
    # AJOUTE CETTE LIGNE EXACTE ICI :
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    
    return response
