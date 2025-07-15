from PIL import Image
import requests
from io import BytesIO

def create_inventory_image(image_urls: list[str], frame_path: str = "resources/frame.png") -> BytesIO:
    frame = Image.open(frame_path).convert("RGBA")
    base = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    item_img_size = 250
    positions = [
        (27, 12), (300, 12), (600, 12),
        (27, 332), (300, 332), (600, 332),
    ]

    for idx, url in enumerate(image_urls[:6]):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            item_img = Image.open(BytesIO(resp.content)).convert("RGBA")
            item_img = item_img.resize((item_img_size, item_img_size))
            x, y = positions[idx]
            base.paste(item_img, (x, y), mask=item_img)
        except Exception as e:
            print(f"Ошибка загрузки изображения {url}: {e}")

    base.paste(frame, (0, 0), mask=frame)

    output = BytesIO()
    base.save(output, format="PNG")
    output.seek(0)
    return output