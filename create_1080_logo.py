import os
from PIL import Image

def make_1080_logo():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    source_icon = os.path.join(app_dir, "app_icon.png")
    out_dir = os.path.join(app_dir, "store_assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "BoxArt_1080x1080.png")

    # Create 1080x1080 RGBA canvas with dark blue background #0F172A
    canvas = Image.new("RGBA", (1080, 1080), (15, 23, 42, 255))

    if os.path.exists(source_icon):
        icon = Image.open(source_icon).convert("RGBA")
        # Resize icon to 600x600 px in center
        icon_resized = icon.resize((600, 600), Image.Resampling.LANCZOS)
        canvas.paste(icon_resized, (240, 240), icon_resized)
    
    canvas.save(out_path, "PNG")
    print("Successfully generated exact 1080x1080 PNG logo at:")
    print(out_path)

if __name__ == "__main__":
    make_1080_logo()
