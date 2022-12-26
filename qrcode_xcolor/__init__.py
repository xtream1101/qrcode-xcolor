"""
These classes have been copied from https://github.com/lincolnloop/python-qrcode
This way they could be modified for the purpose of this library
without having to overwrite the originals
"""

from typing import TYPE_CHECKING, List

import qrcode.image.base
from qrcode.compat.pil import Image, ImageDraw
from qrcode.image.styles.colormasks import QRColorMask
from qrcode.image.styles.moduledrawers import SquareModuleDrawer
from qrcode.image.styles.moduledrawers.base import QRModuleDrawer

if TYPE_CHECKING:
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.main import ActiveWithNeighbors

# When drawing antialiased things, make them bigger and then shrink them down
# to size after the geometry has been drawn.
ANTIALIASING_FACTOR = 4


class XStyledPilImage(qrcode.image.base.BaseImageWithDrawer):
    """
    Styled PIL image builder, default format is PNG.
    The module_drawer should extend the QRModuleDrawer class and implement the
    drawrect_context(self, box, active, context), and probably also the
    initialize function. This will draw an individual "module" or square on
    the QR code.
    The Image can be specified either by path or with a Pillow Image, and if it
    is there will be placed in the middle of the QR code. No effort is done to
    ensure that the QR code is still legible after the image has been placed
    there; Q or H level error correction levels are recommended to maintain
    data integrity A resampling filter can be specified (defaulting to
    PIL.Image.Resampling.LANCZOS) for resizing; see PIL.Image.resize() for possible
    options for this parameter.
    """

    kind = "PNG"

    needs_processing = True
    default_drawer_class = SquareModuleDrawer

    def __init__(self, *args, **kwargs):
        self.back_color = kwargs.get("back_color", (255, 255, 255, 0))
        embeded_image_path = kwargs.get("embeded_image_path", None)
        self.embeded_image = kwargs.get("embeded_image", None)
        self.embeded_image_resample = kwargs.get(
            "embeded_image_resample", Image.Resampling.LANCZOS
        )
        if not self.embeded_image and embeded_image_path:
            self.embeded_image = Image.open(embeded_image_path)

        # the paint_color is the color the module drawer will use to draw upon
        # a canvas During the color mask process, pixels that are paint_color
        # are replaced by a newly-calculated color
        self.paint_color = self.back_color

        super().__init__(*args, **kwargs)

    def new_image(self, **kwargs):
        return Image.new("RGBA", (self.pixel_size, self.pixel_size), self.back_color)

    def init_new_image(self):
        super().init_new_image()

    def process(self):
        if self.embeded_image:
            self.draw_embeded_image()

    def draw_embeded_image(self):
        if not self.embeded_image:
            return
        total_width, _ = self._img.size
        total_width = int(total_width)
        logo_width_ish = int(total_width / 4)
        logo_offset = (
            int((int(total_width / 2) - int(logo_width_ish / 2)) / self.box_size)
            * self.box_size
        )  # round the offset to the nearest module
        logo_position = (logo_offset, logo_offset)
        logo_width = total_width - logo_offset * 2
        region = self.embeded_image
        region = region.resize((logo_width, logo_width), self.embeded_image_resample)
        if "A" in region.getbands():
            self._img.alpha_composite(region, logo_position)
        else:
            self._img.paste(region, logo_position)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = kwargs.get("kind", self.kind)
        if "kind" in kwargs:
            del kwargs["kind"]
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)


class XStyledPilQRModuleDrawer(QRModuleDrawer):
    """
    A base class for StyledPilImage module drawers.
    """

    img: "StyledPilImage"

    def __init__(
        self, front_color=None, inner_eye_color=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.front_color = front_color if front_color else (0, 0, 0, 255)
        self.inner_eye_color = (
            inner_eye_color if inner_eye_color is not None else self.front_color
        )

    def is_eye_center(self, row: int, col: int):
        """
        Returns True if the row/col is in the center of the eye pattern
        """
        border_width = self.img.border * self.img.box_size
        inner_limit = border_width + (self.img.box_size * 4) + self.img.box_size
        # Top Left
        if (border_width + self.img.box_size) < row < inner_limit:
            if (border_width + self.img.box_size) < col < inner_limit:
                return True

        # Top Right
        if (border_width + self.img.box_size) < row < inner_limit:
            if (
                (self.img.size[0] - inner_limit)
                <= col
                < (self.img.size[0] - border_width - (self.img.box_size * 2))
            ):
                return True

        # Bottom Left
        if (
            (self.img.size[0] - inner_limit)
            <= row
            < (self.img.size[0] - border_width - (self.img.box_size * 2))
        ):
            if (border_width + self.img.box_size) < col < inner_limit:
                return True

        return False


class XSquareModuleDrawer(XStyledPilQRModuleDrawer):
    """
    Draws the modules as simple squares
    """

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)

    def drawrect(self, box, is_active: bool):
        if is_active:
            color = (
                self.inner_eye_color
                if self.is_eye_center(box[0][1], box[0][0])
                else self.front_color
            )
            self.imgDraw.rectangle(box, fill=color)


class XGappedSquareModuleDrawer(XStyledPilQRModuleDrawer):
    """
    Draws the modules as simple squares that are not contiguous.
    The size_ratio determines how wide the squares are relative to the width of
    the space they are printed in
    """

    def __init__(self, size_ratio=0.8, **kwargs):
        super().__init__(**kwargs)
        self.size_ratio = size_ratio

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)
        self.delta = (1 - self.size_ratio) * self.img.box_size / 2

    def drawrect(self, box, is_active: bool):
        if is_active:
            color = (
                self.inner_eye_color
                if self.is_eye_center(box[0][1], box[0][0])
                else self.front_color
            )
            smaller_box = (
                box[0][0] + self.delta,
                box[0][1] + self.delta,
                box[1][0] - self.delta,
                box[1][1] - self.delta,
            )
            self.imgDraw.rectangle(smaller_box, fill=color)


class XCircleModuleDrawer(XStyledPilQRModuleDrawer):
    """
    Draws the modules as circles
    """

    circle = None

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)
        self.circle = self.get_circle(self.front_color)
        self.circle_inner_eye = self.get_circle(self.inner_eye_color)

    def get_circle(self, fill_color):
        fake_size = self.img.box_size * ANTIALIASING_FACTOR
        circle = Image.new(
            self.img.mode,
            (fake_size, fake_size),
            self.img.back_color,
        )
        ImageDraw.Draw(circle).ellipse((0, 0, fake_size, fake_size), fill=fill_color)
        return circle.resize(
            (self.img.box_size, self.img.box_size), Image.Resampling.LANCZOS
        )

    def drawrect(self, box, is_active: bool):
        if is_active:
            circle = (
                self.circle_inner_eye
                if self.is_eye_center(box[0][1], box[0][0])
                else self.circle
            )
            self.img._img.paste(circle, (box[0][0], box[0][1]))


class XRoundedModuleDrawer(XStyledPilQRModuleDrawer):
    """
    Draws the modules with all 90 degree corners replaced with rounded edges.

    radius_ratio determines the radius of the rounded edges - a value of 1
    means that an isolated module will be drawn as a circle, while a value of 0
    means that the radius of the rounded edge will be 0 (and thus back to 90
    degrees again).
    """

    needs_neighbors = True

    def __init__(self, radius_ratio=1, **kwargs):
        super().__init__(**kwargs)
        self.radius_ratio = radius_ratio

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)
        self.corner_width = int(self.img.box_size / 2)
        self.setup_corners()

    def setup_corners(self):
        self.colored_shapes = {}
        self.colored_shapes["normal"] = self.set_color_options(self.front_color)
        self.colored_shapes["inner_eye"] = self.set_color_options(self.inner_eye_color)

    def set_color_options(self, fill_color):
        mode = self.img.mode
        shapes = {}
        shapes["square"] = Image.new(
            mode, (self.corner_width, self.corner_width), fill_color
        )

        fake_width = self.corner_width * ANTIALIASING_FACTOR
        radius = self.radius_ratio * fake_width
        diameter = radius * 2
        base = Image.new(
            mode, (fake_width, fake_width), self.img.back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, diameter, diameter), fill=fill_color)
        base_draw.rectangle((radius, 0, fake_width, fake_width), fill=fill_color)
        base_draw.rectangle((0, radius, fake_width, fake_width), fill=fill_color)
        shapes["nw_round"] = base.resize(
            (self.corner_width, self.corner_width), Image.Resampling.LANCZOS
        )
        shapes["sw_round"] = shapes["nw_round"].transpose(
            Image.Transpose.FLIP_TOP_BOTTOM
        )
        shapes["se_round"] = shapes["nw_round"].transpose(Image.Transpose.ROTATE_180)
        shapes["ne_round"] = shapes["nw_round"].transpose(
            Image.Transpose.FLIP_LEFT_RIGHT
        )

        return shapes

    def drawrect(self, box: List[List[int]], is_active: "ActiveWithNeighbors"):
        if not is_active:
            return

        # find rounded edges
        nw_rounded = not is_active.W and not is_active.N
        ne_rounded = not is_active.N and not is_active.E
        se_rounded = not is_active.E and not is_active.S
        sw_rounded = not is_active.S and not is_active.W

        nw = "nw_round" if nw_rounded else "square"
        ne = "ne_round" if ne_rounded else "square"
        se = "se_round" if se_rounded else "square"
        sw = "sw_round" if sw_rounded else "square"

        colored_shape = (
            self.colored_shapes["inner_eye"]
            if self.is_eye_center(box[0][1], box[0][0])
            else self.colored_shapes["normal"]
        )

        self.img._img.paste(colored_shape[nw], (box[0][0], box[0][1]))
        self.img._img.paste(
            colored_shape[ne], (box[0][0] + self.corner_width, box[0][1])
        )
        self.img._img.paste(
            colored_shape[se],
            (box[0][0] + self.corner_width, box[0][1] + self.corner_width),
        )
        self.img._img.paste(
            colored_shape[sw], (box[0][0], box[0][1] + self.corner_width)
        )


class XVerticalBarsDrawer(XStyledPilQRModuleDrawer):
    """
    Draws vertically contiguous groups of modules as long rounded rectangles,
    with gaps between neighboring bands (the size of these gaps is inversely
    proportional to the horizontal_shrink).
    """

    needs_neighbors = True

    def __init__(self, horizontal_shrink=0.8, **kwargs):
        super().__init__(**kwargs)
        self.horizontal_shrink = horizontal_shrink

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)
        self.half_height = int(self.img.box_size / 2)
        self.delta = int((1 - self.horizontal_shrink) * self.half_height)
        self.setup_edges()

    def setup_edges(self):
        self.colored_shapes = {}
        self.colored_shapes["normal"] = self.set_color_options(self.front_color)
        self.colored_shapes["inner_eye"] = self.set_color_options(self.inner_eye_color)

    def set_color_options(self, fill_color):
        shapes = {}
        mode = self.img.mode

        height = self.half_height
        width = height * 2
        shrunken_width = int(width * self.horizontal_shrink)
        shapes["square"] = Image.new(mode, (shrunken_width, height), fill_color)

        fake_width = width * ANTIALIASING_FACTOR
        fake_height = height * ANTIALIASING_FACTOR
        base = Image.new(
            mode, (fake_width, fake_height), self.img.back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, fake_width, fake_height * 2), fill=fill_color)

        shapes["round_top"] = base.resize(
            (shrunken_width, height), Image.Resampling.LANCZOS
        )
        shapes["round_bottom"] = shapes["round_top"].transpose(
            Image.Transpose.FLIP_TOP_BOTTOM
        )

        return shapes

    def drawrect(self, box, is_active: "ActiveWithNeighbors"):
        if is_active:
            # find rounded edges
            top_rounded = not is_active.N
            bottom_rounded = not is_active.S

            top = "round_top" if top_rounded else "square"
            bottom = "round_bottom" if bottom_rounded else "square"

            colored_shape = (
                self.colored_shapes["inner_eye"]
                if self.is_eye_center(box[0][1], box[0][0])
                else self.colored_shapes["normal"]
            )

            self.img._img.paste(colored_shape[top], (box[0][0] + self.delta, box[0][1]))
            self.img._img.paste(
                colored_shape[bottom],
                (box[0][0] + self.delta, box[0][1] + self.half_height),
            )


class XHorizontalBarsDrawer(XStyledPilQRModuleDrawer):
    """
    Draws horizontally contiguous groups of modules as long rounded rectangles,
    with gaps between neighboring bands (the size of these gaps is inversely
    proportional to the vertical_shrink).
    """

    needs_neighbors = True

    def __init__(self, vertical_shrink=0.8, **kwargs):
        super().__init__(**kwargs)
        self.vertical_shrink = vertical_shrink

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.half_width = int(self.img.box_size / 2)
        self.delta = int((1 - self.vertical_shrink) * self.half_width)
        self.setup_edges()

    def setup_edges(self):
        self.colored_shapes = {}
        self.colored_shapes["normal"] = self.set_color_options(self.front_color)
        self.colored_shapes["inner_eye"] = self.set_color_options(self.inner_eye_color)

    def set_color_options(self, fill_color):
        shapes = {}
        mode = self.img.mode

        width = self.half_width
        height = width * 2
        shrunken_height = int(height * self.vertical_shrink)
        shapes["square"] = Image.new(mode, (width, shrunken_height), fill_color)

        fake_width = width * ANTIALIASING_FACTOR
        fake_height = height * ANTIALIASING_FACTOR
        base = Image.new(
            mode, (fake_width, fake_height), self.img.back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, fake_width * 2, fake_height), fill=fill_color)

        shapes["round_left"] = base.resize(
            (width, shrunken_height), Image.Resampling.LANCZOS
        )
        shapes["round_right"] = shapes["round_left"].transpose(
            Image.Transpose.FLIP_LEFT_RIGHT
        )

        return shapes

    def drawrect(self, box, is_active: "ActiveWithNeighbors"):
        if is_active:
            # find rounded edges
            left_rounded = not is_active.W
            right_rounded = not is_active.E

            left = "round_left" if left_rounded else "square"
            right = "round_right" if right_rounded else "square"
            colored_shape = (
                self.colored_shapes["inner_eye"]
                if self.is_eye_center(box[0][1], box[0][0])
                else self.colored_shapes["normal"]
            )

            self.img._img.paste(
                colored_shape[left], (box[0][0], box[0][1] + self.delta)
            )
            self.img._img.paste(
                colored_shape[right],
                (box[0][0] + self.half_width, box[0][1] + self.delta),
            )
