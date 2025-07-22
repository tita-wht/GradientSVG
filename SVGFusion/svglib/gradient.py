# グラデーション関係クラス群
from __future__ import annotations
from .geom import *
from .color import Color
from typing import List, Union
from xml.dom import minidom
from .utils import persentage_to_float
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

        offset = persentage_to_float(offset_str, default=0.0)
        opacity = persentage_to_float(opacity_str, default=1.0)

        color = Color(Color.from_str(color_str))
        color.a = opacity

        return Stop(offset, color)

    # NOTE: 可視化用メソッド_bbox_vizなどを実装する


class SVGGradient:
    def __init__(self, id_name:str, gradient_type:str, stops:List[Stop] = None):
        self.id = id_name # fill/stroke="id"で指定
        self.stops = stops
        # NOTE: when the number of stops is 1, it is a solid color (its a normal fill / single color)
        self.spreadmethod = "pad" # or "reflect" or "repeat"
        # FIXME: spreadmethodは後で
        # pad: 最外端のstop以降の座標は単色で塗りつぶし
        # reflect: 最外端のstop以降は方向を逆転してなめらかにグラデーション
        # repeat: 最外端のstopで始めのstopに戻る
        # ただし、x1, y1, x2, y2の規定値ではグラデーションがシェイプの外端まで到達するので意味なし。

        # TODO
        self.units = None # グラデーションを適用する上位の座標系
        self.transform =None # グラデーションに対する追加の座標変換

    def add_stop(self, offset:Union[int, float], color:Color):
        self.stops.append(Stop(offset, color))

    def get_stops(self):
        return self.stops

    def __repr__(self):
        return f"SVGGradient(type={self.gradient_type}, stops={self.stops})"
        # Add bounding boxes for each primitive

    @staticmethod
    def from_xml(x: minidom.Element):
        raise NotImplementedError("This method should be implemented in subclasses")
    
    def to_tensor(self, *args, **kwargs):
        raise NotImplementedError
    
    def copy(self):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError
    
class SVGLinearGradient(SVGGradient):
    # NOTE: x1, y1, x2, y2は0~1(0%~100%)を仮定。gradientUnits属性がデフォルト値以外を取るように拡張する場合はdirection関係を修正する必要あり。
    def __init__(self, id_name:str, x1:float=0.0, y1:float=0.0, x2:float=1.0, y2:float=0.0, stops:List[Stop] = None):
        super().__init__(id_name, "linear", stops)
        self.pos1 = Point(x1, y1)  # start position
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        """
        x1, y1: start position of the gradient
        x2, y2: end position of the gradient
        グラデーションの方向を決定するとともに、グラデーションの開始地点・終了地点も決める。グラデーションの範囲外に関してはSVGGradientのspreadmethodに従う。
        0~1(0%~100%)で示す。→gradientUnits属性のデフォルト値が相対座標。
        ユーザ座標系（絶対座標）に変えることも可能だが、やらない方が無難。
        """

    @property
    def origin(self):
        return np.array([self.x1, self.y1], dtype=np.float32)
    
    @property
    def direction(self):
        return np.array([self.x2 - self.x1, self.y2 - self.y1], dtype=np.float32)

    def __repr__(self):
        return f"SVGLinearGradient(id={self.id}, x1={self.x1}, y1={self.y1}, x2={self.x2}, y2={self.y2}, stops={self.stops})"

    def fit_bbox(self, bbox:Bbox):
        # 方向を維持しつつ、bboxに合わせてx1, y1, x2, y2を最大化する
        raise NotImplementedError("This method should be implemented in subclasses")

    def to_str(self, *args, **kwargs):
        fill_attr = f'<linearGradient id="{self.id}" x1="{self.x1}" y1="{self.y1}" x2="{self.x2}" y2="{self.y2}" '
        if self.spreadmethod != "pad":
            fill_attr += f'spreadMethod="{self.spreadmethod}" '
        fill_attr += '>'
        for stop in self.stops:
            fill_attr += stop.to_str()
        fill_attr += '</linearGradient>'
        return fill_attr

    def to_tensor(self, PAD_VAL=-1, *args, **kwargs):
        """ return torch.tensor([[x1, y1, x2, y2], [*self.stops[i].to_tensor() for i in range(len(self.stops))]]) """
        stops_tensor = torch.stack([stop.to_tensor() for stop in self.stops], dim=0)
        if len(stops_tensor) == 0:
            stops_tensor = torch.tensor([[PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL]], dtype=torch.float32)
        origin_tensor = torch.tensor([self.x1, self.y1], dtype=torch.float32)
        direction_tensor = torch.tensor([self.x2 - self.x1, self.y2 - self.y1], dtype=torch.float32)
        return origin_tensor, direction_tensor, stops_tensor

    @staticmethod
    def from_direction(origin, direction):
        x1, y1 = origin
        x2, y2 = origin + direction
        return x1, y1, x2, y2

    @staticmethod
    def from_xml(x: minidom.Element):
        id_name = x.getAttribute("id")
        x1 = persentage_to_float(x.getAttribute("x1"), default=0.0)
        y1 = persentage_to_float(x.getAttribute("y1"), default=0.0)
        x2 = persentage_to_float(x.getAttribute("x2"), default=1.0)
        y2 = persentage_to_float(x.getAttribute("y2"), default=0.0)

        stops = []
        for stop_elem in x.getElementsByTagName("stop"):
            stops.append(Stop.from_xml(stop_elem))

        return SVGLinearGradient(id_name, x1, y1, x2, y2, stops)

        


# とりあえず、読み込みと書き出しをできるようにして、stopをテンソルとして扱えるようにする。
