from __future__ import annotations
import numpy as np
from typing import Union, List, Tuple
import torch
Num = Union[int, float]
RGBA = Tuple[Num, Num, Num, Num]
RGB = Tuple[Num, Num, Num]
float_type = (int, float, np.float32, np.float64)

class Color:
    num_args = 4

    def __init__(self, rgb:List[Num] = None, alpha:Num = 1.0):
        # NOTE: alphaを0~255で表現する
        if rgb is None:
            rgb = [0.0, 0.0, 0.0] # black
        elif len(rgb) > 3:
            rgb = rgb[:3]  # truncate to first 3 elements
        self.rgb = np.array(rgb, dtype=np.float32)
        self.a = np.array(alpha, dtype=np.float32)

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
        return np.concatenate((self.rgb, self.alpha)).tolist() 

    def __repr__(self):
        return f"Color({self.rgba}.to_str())"

    def copy(self):
        raise Color(self.rgb.copy(), self.alpha.copy())

    def to_str(self):
        return f"{self.rgba[0]:.3f} {self.rgba[1]:.3f} {self.rgba[2]:.3f} {self.alpha[0]:.3f}"

    def to_tensor(self):
        # return rgba
        return torch.tensor(self.rgba, dtype=torch.float32)

    @staticmethod
    def from_tensor(vector: torch.Tensor):
        return Color(vector.tolist())

    def numericalize_rgb(self, n=256):
        self.rgb = self.rgb.round().clip(min=0, max=n-1)
        return self
    