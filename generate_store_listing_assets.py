import os
from PIL import Image, ImageDraw, ImageFont

def generate_listing_assets():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    source_icon_path = os.path.join(app_dir, "app_icon.png")
    output_dir = os.path.join(app_dir, "store_assets")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(source_icon_path):
        print(f"Error: {source_icon_path} not found.")
        return

    icon = Image.open(source_icon_path).convert("RGBA")

    # 1. 1080x1080 Box Art
    box_art = Image.new("RGBA", (1080, 1080), (17, 24, 39, 255))
    icon_resized = icon.resize((600, 600), Image.Resampling.LANCZOS)
    box_art.paste(icon_resized, (240, 240), icon_resized)
    box_art.save(os.path.join(output_dir, "BoxArt_1080x1080.png"), "PNG")
    print("Generated: BoxArt_1080x1080.png (1080x1080 px)")

    # 2. 720x1080 Poster Art
    poster_art = Image.new("RGBA", (720, 1080), (17, 24, 39, 255))
    icon_poster = icon.resize((480, 480), Image.Resampling.LANCZOS)
    poster_art.paste(icon_poster, (120, 300), icon_poster)
    poster_art.save(os.path.join(output_dir, "PosterArt_720x1080.png"), "PNG")
    print("Generated: PosterArt_720x1080.png (720x1080 px)")

    # 3. 1366x768 App Screenshot Mockup
    ss = Image.new("RGBA", (1366, 768), (15, 23, 42, 255))
    draw = ImageDraw.Draw(ss)
    
    # Outer App Window
    draw.rectangle([100, 80, 1266, 688], fill=(30, 41, 59, 255), outline=(71, 85, 105, 255), width=2)
    # Header bar
    draw.rectangle([100, 80, 1266, 140], fill=(15, 23, 42, 255))
    
    icon_ss = icon.resize((40, 40), Image.Resampling.LANCZOS)
    ss.paste(icon_ss, (120, 90), icon_ss)

    # Pop-up card in center
    draw.rectangle([433, 234, 933, 534], fill=(17, 24, 39, 255), outline=(52, 211, 153, 255), width=2)
    
    ss.save(os.path.join(output_dir, "Screenshot_1366x768.png"), "PNG")
    print("Generated: Screenshot_1366x768.png (1366x768 px)")

if __name__ == "__main__":
    generate_listing_assets()
