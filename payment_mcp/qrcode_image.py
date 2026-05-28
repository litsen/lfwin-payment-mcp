from base64 import b64encode
from io import BytesIO

import qrcode


PNG_DATA_URL_PREFIX = "data:image/png;base64,"


def make_png_base64(value: str) -> str:
    image = qrcode.make(value)
    output = BytesIO()
    image.save(output, format="PNG")
    return b64encode(output.getvalue()).decode("ascii")


def make_png_data_url(value: str) -> str:
    return f"{PNG_DATA_URL_PREFIX}{make_png_base64(value)}"
