from base64 import b64encode
from io import BytesIO

import qrcode


def make_png_data_url(value: str) -> str:
    image = qrcode.make(value)
    output = BytesIO()
    image.save(output, format="PNG")
    encoded = b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
