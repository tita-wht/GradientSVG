from __future__ import annotations
import numpy as np
from typing import Union, List, Any
import torch
Num = Union[int, float]
float_type = (int, float, np.float32, np.float64)

class Color:
    num_args = 4

    def __init__(self, rgb:Union[List[Num], str, None] = None, alpha:Num = None):
        # NOTE: alphaのみ0~1
        # 埋め込み時にはかえたほうがいいかもね
        if rgb is None:
            rgb = [0, 0, 0] # black
        elif isinstance(rgb, str):
            rgb, alpha = Color.from_str(rgb)
        elif len(rgb) > 3:
            rgb = rgb[:3]  # truncate to first 3 elements
        self.rgb = np.array(rgb, dtype=np.float32)

        alpha = alpha if alpha is not None else 1.0
        self.a = np.float32(alpha)
        # MEMO: alphaについて
        # 引数のalphaが有効な場合 → alpha
        # rgbaで指定される場合    → alpha -> a
        # rgbaもalphaもない場合   → 1.0 (完全に不透明)

    @property
    def r(self):
        return self.rgba[0]
    @property
    def g(self):
        return self.rgba[1]
    @property
    def b(self):
        return self.rgba[2]
    @property
    def rgba(self) -> List[Num]:
        return np.concatenate((self.rgb, [self.a])) 

    def __repr__(self):
        txt = f"{self.rgba[0]:.3f} {self.rgba[1]:.3f} {self.rgba[2]:.3f} {self.rgba[3]:.3f}"
        return f"Color({txt})"

    def copy(self):
        return Color(self.rgb.copy(), self.a.copy())

    def to_str(self):
        rgb = self.rgb.round().clip(min=0, max=255)
        if self.a == 1.0:
            str = f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
        else:
            str = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{self.a})"
        return str

    def to_tensor(self):
        # return rgba
        return torch.tensor(self.rgba, dtype=torch.float32)

    @staticmethod
    def from_tensor(vector: torch.Tensor):
        return Color(vector.tolist())

    def numericalize_rgb(self, n=256):
        self.rgb = self.rgb.round().clip(min=0, max=n-1)
        return self
    
    @staticmethod
    def from_str(str:str):
        if str.startswith("#"):
            rgb, a = Color._from_hex(str)
        elif str.startswith("rgb"):
            rgb, a = Color._from_color_list(str)
        else:
            rgb, a = Color._from_color_name(str)
        return Color(rgb, a)
    
    @staticmethod
    def _from_hex(hex_color: str):
        """Convert a hex color string to an RGB color."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        elif len(hex_color) == 3:
            r = int(hex_color[0] * 2, 16)
            g = int(hex_color[1] * 2, 16)
            b = int(hex_color[2] * 2, 16)
        else:
            raise ValueError("Invalid hex color format")
        rgb = [r, g, b]
        return (rgb, 1.0)
    
    @staticmethod
    def _from_color_name(color_name: str):
        """Convert a color name to an RGB color."""
        color_name = color_name.lower()
        if color_name in COLOR_RGB_DICT:
            rgb = COLOR_RGB_DICT[color_name]
            return (list(rgb), 1.0)
        else:
            raise ValueError(f"Color name '{color_name}' not recognized.")
        
    @staticmethod
    def _from_color_list(str: str):
        # rgb(r,g,b) or rgba(r,g,b,a)
        s = str.strip().lower()
        if s.startswith("rgba"):
            values = s[s.find("(")+1:s.find(")")].split(",")
            if len(values) != 4:
                raise ValueError("Invalid rgba color string")
            r, g, b, a = [float(v.strip()) for v in values]
            return ([r, g, b], a)
        elif s.startswith("rgb"):
            values = s[s.find("(")+1:s.find(")")].split(",")
            if len(values) != 3:
                raise ValueError("Invalid rgb color string")
            r, g, b = [float(v.strip()) for v in values]
            return ([r, g, b], 1.0)
    

COLOR_RGB_DICT = {
    "aliceblue":        (240, 248, 255),
    "antiquewhite":     (250, 235, 215),
    "aqua":             (0, 255, 255),
    "aquamarine":       (127, 255, 212),
    "azure":            (240, 255, 255),
    "beige":            (245, 245, 220),
    "bisque":           (255, 228, 196),
    "black":            (0, 0, 0),
    "blanchedalmond":   (255, 235, 205),
    "blue":             (0, 0, 255),
    "blueviolet":       (138, 43, 226),
    "brown":            (165, 42, 42),
    "burlywood":        (222, 184, 135),
    "cadetblue":        (95, 158, 160),
    "chartreuse":       (127, 255, 0),
    "chocolate":        (210, 105, 30),
    "coral":            (255, 127, 80),
    "cornflowerblue":   (100, 149, 237),
    "cornsilk":         (255, 248, 220),
    "crimson":          (220, 20, 60),
    "cyan":             (0, 255, 255),
    "darkblue":         (0, 0, 139),
    "darkcyan":         (0, 139, 139),
    "darkgoldenrod":    (184, 134, 11),
    "darkgray":         (169, 169, 169),
    "darkgreen":        (0, 100, 0),
    "darkgrey":         (169, 169, 169),
    "darkkhaki":        (189, 183, 107),
    "darkmagenta":      (139, 0, 139),
    "darkolivegreen":   (85, 107, 47),
    "darkorange":       (255, 140, 0),
    "darkorchid":       (153, 50, 204),
    "darkred":          (139, 0, 0),
    "darksalmon":       (233, 150, 122),
    "darkseagreen":     (143, 188, 143),
    "darkslateblue":    (72, 61, 139),
    "darkslategray":    (47, 79, 79),
    "darkslategrey":    (47, 79, 79),
    "darkturquoise":    (0, 206, 209),
    "darkviolet":       (148, 0, 211),
    "deeppink":         (255, 20, 147),
    "deepskyblue":      (0, 191, 255),
    "dimgray":          (105, 105, 105),
    "dimgrey":          (105, 105, 105),
    "dodgerblue":       (30, 144, 255),
    "firebrick":        (178, 34, 34),
    "floralwhite":      (255, 250, 240),
    "forestgreen":      (34, 139, 34),
    "fuchsia":          (255, 0, 255),
    "gainsboro":        (220, 220, 220),
    "ghostwhite":       (248, 248, 255),
    "gold":             (255, 215, 0),
    "goldenrod":        (218, 165, 32),
    "gray":             (128, 128, 128),
    "green":            (0, 128, 0),
    "greenyellow":      (173, 255, 47),
    "grey":             (128, 128, 128),
    "honeydew":         (240, 255, 240),
    "hotpink":          (255, 105, 180),
    "indianred":        (205, 92, 92),
    "indigo":           (75, 0, 130),
    "ivory":            (255, 255, 240),
    "khaki":            (240, 230, 140),
    "lavender":         (230, 230, 250),
    "lavenderblush":    (255, 240, 245),
    "lawngreen":        (124, 252, 0),
    "lemonchiffon":     (255, 250, 205),
    "lightblue":        (173, 216, 230),
    "lightcoral":       (240, 128, 128),
    "lightcyan":        (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray":        (211, 211, 211),
    "lightgreen":       (144, 238, 144),
    "lightgrey":        (211, 211, 211),
    "lightpink":        (255, 182, 193),
    "lightsalmon":      (255, 160, 122),
    "lightseagreen":    (32, 178, 170),
    "lightskyblue":     (135, 206, 250),
    "lightslategray":   (119, 136, 153),
    "lightslategrey":   (119, 136, 153),
    "lightsteelblue":   (176, 196, 222),
    "lightyellow":      (255, 255, 224),
    "lime":             (0, 255, 0),
    "limegreen":        (50, 205, 50),
    "linen":            (250, 240, 230),
    "magenta":          (255, 0, 255),
    "maroon":           (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue":       (0, 0, 205),
    "mediumorchid":     (186, 85, 211),
    "mediumpurple":     (147, 112, 219),
    "mediumseagreen":   (60, 179, 113),
    "mediumslateblue":  (123, 104, 238),
    "mediumspringgreen":(0, 250, 154),
    "mediumturquoise":  (72, 209, 204),
    "mediumvioletred":  (199, 21, 133),
    "midnightblue":     (25, 25, 112),
    "mintcream":        (245, 255, 250),
    "mistyrose":        (255, 228, 225),
    "moccasin":         (255, 228, 181),
    "navajowhite":      (255, 222, 173),
    "navy":             (0, 0, 128),
    "oldlace":          (253, 245, 230),
    "olive":            (128, 128, 0),
    "olivedrab":        (107, 142, 35),
    "orange":           (255, 165, 0),
    "orangered":        (255, 69, 0),
    "orchid":           (218, 112, 214),
    "palegoldenrod":    (238, 232, 170),
    "palegreen":        (152, 251, 152),
    "paleturquoise":    (175, 238, 238),
    "palevioletred":    (219, 112, 147),
    "papayawhip":       (255, 239, 213),
    "peachpuff":        (255, 218, 185),
    "peru":             (205, 133, 63),
    "pink":             (255, 192, 203),
    "plum":             (221, 160, 221),
    "powderblue":       (176, 224, 230),
    "purple":           (128, 0, 128),
    "rebeccapurple":    (102, 51, 153),
    "red":              (255, 0, 0),
    "rosybrown":        (188, 143, 143),
    "royalblue":        (65, 105, 225),
    "saddlebrown":      (139, 69, 19),
    "salmon":           (250, 128, 114),
    "sandybrown":       (244, 164, 96),
    "seagreen":         (46, 139, 87),
    "seashell":         (255, 245, 238),
    "sienna":           (160, 82, 45),
    "silver":           (192, 192, 192),
    "skyblue":          (135, 206, 235),
    "slateblue":        (106, 90, 205),
    "slategray":        (112, 128, 144),
    "slategrey":        (112, 128, 144),
    "snow":             (255, 250, 250),
    "springgreen":      (0, 255, 127),
    "steelblue":        (70, 130, 180),
    "tan":              (210, 180, 140),
    "teal":             (0, 128, 128),
    "thistle":          (216, 191, 216),
    "tomato":           (255, 99, 71),
    "turquoise":        (64, 224, 208),
    "violet":           (238, 130, 238),
    "wheat":            (245, 222, 179),
    "white":            (255, 255, 255),
    "whitesmoke":       (245, 245, 245),
    "yellow":           (255, 255, 0),
    "yellowgreen":      (154, 205, 50),
}
