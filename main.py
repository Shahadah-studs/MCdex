from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

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

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Lire les données brutes envoyées par le formulaire HTML de Vercel
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # 2. Convertir les données textuelles en dictionnaire Python
        fields = parse_qs(post_data)
        
        # Récupérer les valeurs (parse_qs renvoie des listes, on prend le premier élément)
        block_name = fields.get('block_name', ['elite_block'])[0]
        block_type = fields.get('block_type', ['normal'])[0]
        
        # 3. Nettoyer le nom pour Minecraft (minuscules, pas d'espaces ni caractères interdits)
        block_id = block_name.lower().replace(" ", "_")
        for char in ['/', '\\', '"', "'", '!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
            block_id = block_id.replace(char, "")
            
        # 4. Logique des paliers (Tiers) de ton IA
        if block_type == "god_tier":
            destroy_time = 50.0
            light_level = 15
        elif block_type == "light":
            destroy_time = 1.0
            light_level = 10
        else:
            destroy_time = 3.0
            light_level = 0
            
        # 5. Injecter les données dans le modèle officiel de bloc
        generated_code = MINECRAFT_BLOCK_TEMPLATE.format(
            block_id=block_id,
            destroy_time=destroy_time,
            light_level=light_level
        )
        
        # 6. Envoyer la réponse HTTP au navigateur de ton joueur
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Construction de la page de rendu pour ton iframe
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
            <div class="title">⚡ SHS ELITE AI - MINECRAFT CODE SUCCESSFUL:</div>
            <p>Copy this into your Behavior Pack (components/blocks/{block_id}.json):</p>
            <pre>{generated_code}</pre>
            <br>
            <a href="javascript:history.back()" style="color: #ffcc00; text-decoration: none; font-weight: bold;">[ ← GENERATE ANOTHER BLOCK ]</a>
        </body>
        </html>
        """
        
        # Écriture finale dans l'iframe
        self.wfile.write(html_response.encode('utf-8'))
        return
