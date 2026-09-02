import os
from PIL import Image

def generate_assets():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    source_icon_path = os.path.join(app_dir, "app_icon.png")
    output_dir = os.path.join(app_dir, "store_assets")

    if not os.path.exists(source_icon_path):
        print(f"Error: {source_icon_path} not found.")
        return

    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(source_icon_path)

    sizes = {
        "Square44x44Logo.png": (44, 44),
        "Square50x50Logo.png": (50, 50),
        "Square150x150Logo.png": (150, 150),
        "Square300x300Logo.png": (300, 300),
        "StoreLogo.png": (500, 500)
    }

    generated_files = []
    for filename, size in sizes.items():
        out_path = os.path.join(output_dir, filename)
        resized_img = img.resize(size, Image.Resampling.LANCZOS)
        resized_img.save(out_path, format="PNG")
        generated_files.append((filename, out_path, size))
        print(f"Generated: {filename} ({size[0]}x{size[1]} px)")

    print(f"\nSuccessfully generated {len(generated_files)} Microsoft Store asset images in:\n{output_dir}\n")

if __name__ == "__main__":
    generate_assets()
