from PIL import Image, ImageDraw
import hashlib

def _color_from_name(name, light_level=0):
    # Deterministic color from name
    h = hashlib.sha256(name.encode('utf-8')).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    # apply light level (0-15) to brighten
    factor = 1.0 + (light_level / 30.0)
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return (r, g, b)


def render_block_preview(block_id: str, light_level: int = 0, size: int = 256):
    """
    Render a simple isometric-style 3-face cube preview and return a PIL Image.
    This is a fast approximation for a visual preview (not a Minecraft renderer).
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # compute face polygons (simple pseudo-isometric)
    cx = size // 2
    cy = size // 2 + size // 8
    s = size // 3

    # top
    top = [(cx, cy - s), (cx + s, cy - s//2), (cx, cy), (cx - s, cy - s//2)]
    # right
    right = [(cx + s, cy - s//2), (cx + s, cy + s//2), (cx, cy + s), (cx, cy)]
    # left
    left = [(cx - s, cy - s//2), (cx, cy), (cx, cy + s), (cx - s, cy + s//2)]

    base_color = _color_from_name(block_id, light_level)
    # shade faces
    def shade(c, factor):
        return tuple(min(255, int(round(ch * factor))) for ch in c)

    top_color = shade(base_color, 1.15)
    right_color = shade(base_color, 0.9)
    left_color = shade(base_color, 0.75)

    draw.polygon(left, fill=left_color)
    draw.polygon(right, fill=right_color)
    draw.polygon(top, fill=top_color)

    # outline
    outline_color = (20, 20, 20, 180)
    draw.line(top + [top[0]], fill=outline_color, width=2)
    draw.line(right + [right[0]], fill=outline_color, width=2)
    draw.line(left + [left[0]], fill=outline_color, width=2)

    return img

if __name__ == '__main__':
    # quick standalone test
    img = render_block_preview('test_block', 10)
    img.save('preview_test.png')
