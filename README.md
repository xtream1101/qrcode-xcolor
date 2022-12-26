# QRCode XColor

_Note: This does not work with the qrcode version 7.3.1 in pypi. pypi will not allow git sources in the setup.py requirments so mush be manually installed_

**Install qrcode from master branch**
```bash
pip install git+https://github.com/lincolnloop/python-qrcode.git@8a37658d68dae463479ee88e96ee3f1f53a16f54
```

This library recreates a few of the `moduledrawers` classes already found in https://github.com/lincolnloop/python-qrcode.  

This was done to greatly speed up the generation of creating colored qrcodes, as well as supporting for different colors and styles for the location marker in the corners.  

Using these custom classes you do lose support for the full features of the `color_mask` argument in the original `QRCode` library like having the colors be a gradient across the qrcode.  

I chose for speed over having that feature with still getting full color and transparency support of the qrcode.  


All supported module drawers:

```python
from qrcode_xcolor import (
    XStyledPilImage,
    XSquareModuleDrawer,
    XGappedSquareModuleDrawer,
    XCircleModuleDrawer,
    XRoundedModuleDrawer,
    XVerticalBarsDrawer,
    XHorizontalBarsDrawer
)
```
Here are some examples of the speed difference:

```python
import time

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import GappedSquareModuleDrawer, RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

from qrcode_xcolor import XStyledPilImage, XGappedSquareModuleDrawer, XRoundedModuleDrawer

st = time.time()
qr = qrcode.QRCode()
qr.add_data("https://example.com")
img = qr.make_image(
    image_factory=StyledPilImage,
    color_mask=SolidFillColorMask(
        front_color=(59, 89, 152),
        back_color=(255, 255, 255),
    ),
    module_drawer=GappedSquareModuleDrawer(),
    eye_drawer=RoundedModuleDrawer(),
    embeded_image_path='docs/gitlab.png',
)
img.save("qrcode_color_mask.png")
print(f"qrcode color_mask: {time.time() - st:.4f}s")


st = time.time()
qr = qrcode.QRCode()
qr.add_data("https://example.com")
# The 4th value in all the colors is the opacity the color should use (0=clear <--> 255=solid)
img = qr.make_image(
    # Custom image factory
    image_factory=XStyledPilImage,
    back_color=(255, 255, 255, 255),  # Background color with opacity support
    module_drawer=XGappedSquareModuleDrawer(
        front_color=(59, 89, 152, 255),
    ),
    eye_drawer=XRoundedModuleDrawer(
        front_color=(255, 110, 0, 255),
        inner_eye_color=(65, 14, 158, 255),  # Only valid with the eye_drawer
    ),
    embeded_image_path='docs/gitlab.png',  # Still supports embedding logos in the middle
)
img.save("qrcode-xcolor.png")
print(f"qrcode-xcolor: {time.time() - st:.4f}s")
```

From this test we get the results (exact timings will vary but the difference is always there):
```
qrcode color_mask: 0.5071s
```
![qrcode color_mask](docs/qrcode_color_mask.png "qrcode color_mask")
```
qrcode-xcolor: 0.0430s
```
![qrcode-xcolor](docs/qrcode-xcolor.png "qrcode-xcolor")
