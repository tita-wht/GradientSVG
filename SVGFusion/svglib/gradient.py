# グラデーション関係クラス群
from __future__ import annotations
from .geom import *
from .color import Color
from typing import List, Union
from xml.dom import minidom
import torch


class Stop:
    def __init__(self, offset:Union[int, float], color:Color):
        self.offset = offset # 0.0 ~ 1.0
        self.color = color # RGBA
        # MEMO: 本来style属性によって再利用性を高めるが、実装が面倒なので後で。
    
    @property
    def content(self):
        return np.array([*self.color.rgba, self.offset], dtype=np.float32)
    
    def __repr__(self):
        return f"Stop(offset={self.offset}, stop-color={self.color})"
    
    def copy(self):
        return Stop(self.offset, self.color.copy())
    
    def to_str(self, *args, **kwargs):
        return f'<stop offset="{self.offset}" stop-color="{self.color.to_str()}" />'
    
    def to_tensor(self, *args, **kwargs):
        """ return torch.tensor([*self.color.rgba, self.offset]) """
        return torch.tensor([*self.color.rgba, self.offset], dtype=torch.float32)

    @staticmethod
    def from_xml(x: minidom.Element):        
        offset_str = x.getAttribute("offset")
        color_str = x.getAttribute("stop-color")
        opacity_str = x.getAttribute("stop-opacity")

        if offset_str.endswith('%'):
            offset = float(offset_str[:-1]) / 100.0
        elif offset_str == "":
            offset = 0.0
        else:
            offset = max(0.0, min(float(offset_str), 1.0)) # Clamp to [0.0, 1.0]

        if opacity_str.endswith('%'):
            opacity = float(opacity_str[:-1]) / 100.0
        elif opacity_str == "":
            opacity = 1.0
        else:
            opacity = max(0.0, min(float(opacity_str), 1.0))

        color = Color.from_str(color_str)
        color.a = opacity

        return Stop(offset, color)

    # NOTE: 可視化用メソッド_bbox_vizなどを実装する


class SVGGradient:
    def __init__(self, id_name:str, gradient_type:str, stops:List[Stop] = None):
        self.id = id_name
        self.gradient_type = gradient_type
        self.stops = stops

    def add_stop(self, offset, color):
        self.stops.append({'offset': offset, 'color': color})

    def get_stops(self):
        return self.stops

    def __repr__(self):
        return f"SVGGradient(type={self.gradient_type}, stops={self.stops})"
        # Add bounding boxes for each primitive
