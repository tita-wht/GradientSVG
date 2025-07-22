# グラデーション関係クラス群
from __future__ import annotations
from .geom import *
from .color import Color
from typing import List, Union
from xml.dom import minidom
from .graphics.utils import persentage_to_float, get_rule
import torch


class Stop:
    ATTRS = ["offset", "stop-color", "stop-opacity"]

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
        return f'\t<stop offset="{self.offset}" stop-color="{self.color.to_str()}" />\n'
    
    def to_tensor(self, *args, **kwargs):
        """ return torch.tensor([*self.color.rgba, self.offset]) """
        return torch.tensor([*self.color.rgba, self.offset], dtype=torch.float32)

    @staticmethod
    def from_xml(x: minidom.Elemen, rules_dict=None, *args, **kwargs):
        class_str = x.getAttribute("class")
        attrs = {}
        if class_str:
            attrs = get_rule(rules_dict, class_str, selector_type='class')

        for attr in Stop.ATTRS: # selector <- directly attrs
            if x.hasAttribute(attr):
                attrs[attr] = x.getAttribute(attr)
            if attr not in attrs:
                attrs[attr] = ""

        offset = persentage_to_float(attrs["offset"], default=0.0)
        rgb, a = Color.from_str(attrs["stop-color"])
        if attrs["stop-opacity"]:
            a = persentage_to_float(attrs["stop-opacity"], default=1.0)
        color = Color(rgb, a)

        return Stop(offset, color)

    # NOTE: 可視化用メソッド_bbox_vizなどを実装する


class SVGGradient:
    ATTRS = ["id", "gradientUnits", "gradientTransform", "spreadMethod"]
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
    def from_xml(x: minidom.Element, *args, **kwargs):
        raise NotImplementedError("This method should be implemented in subclasses")
    
    def to_tensor(self, *args, **kwargs):
        raise NotImplementedError
    
    def copy(self):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError
    
class SVGLinearGradient(SVGGradient):
    ATTRS = SVGGradient.ATTRS + ["x1", "y1", "x2", "y2"]
    # NOTE: x1, y1, x2, y2は0~1(0%~100%)を仮定。gradientUnits属性がデフォルト値以外を取るように拡張する場合はdirection関係を修正する必要あり。
    def __init__(self, id_name:str, x1:float=0.0, y1:float=0.0, x2:float=1.0, y2:float=0.0, stops:List[Stop] = None):
        super().__init__(id_name, "linear", stops)
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
        fill_attr += '>\n'
        for stop in self.stops:
            fill_attr += stop.to_str()
        fill_attr += '</linearGradient>\n'
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
    def from_xml(x: minidom.Element, rules_dict=None, *args, **kwargs):
        id_name = x.getAttribute("id")
        x1 = persentage_to_float(x.getAttribute("x1"), default=0.0)
        y1 = persentage_to_float(x.getAttribute("y1"), default=0.0)
        x2 = persentage_to_float(x.getAttribute("x2"), default=1.0)
        y2 = persentage_to_float(x.getAttribute("y2"), default=0.0)

        stops = []
        for stop_elem in x.getElementsByTagName("stop"):
            stops.append(Stop.from_xml(stop_elem, rules_dict=rules_dict))

        return SVGLinearGradient(id_name, x1, y1, x2, y2, stops)
    
class SVGRadialGradient(SVGGradient):
    ATTRS = SVGGradient.ATTRS + ["cx", "cy", "r", "fx", "fy", "fr"]

    def __init__(self, id_name:str, cx:float=0.5, cy:float=0.5, r:float=1.0, fx:float=None, fy:float=None, fr:float=None, stops:List[Stop] = None):
        super().__init__(id_name, "radial", stops)
        self.cx = cx  # 中心のx座標
        self.cy = cy  # 中心のy座標
        self.r = r    # 半径
        self.fx = fx if fx is not None else cx  # グラデーションの開始円の中心座標
        self.fy = fy if fy is not None else cy
        self.fr = fr if fr is not None else r  # グラデーションの開始円半径
    
    @property
    def origin_circle(self):
        return np.array([self.fx, self.fy, self.fr], dtype=np.float32)
    
    @property
    def dist_circle(self):
        return np.array([self.cx, self.cy, self.r], dtype=np.float32)

    def __repr__(self):
        return f"SVGRadialGradient(id={self.id}, cx={self.cx}, cy={self.cy}, r={self.r}, fx={self.fx}, fy={self.fy}, stops={self.stops})"

    def to_str(self, *args, **kwargs):
        fill_attr = f'<radialGradient id="{self.id}" cx="{self.cx}" cy="{self.cy}" r="{self.r}" '
        if self.fx != self.cx or self.fy != self.cy:
            fill_attr += f'fx="{self.fx}" fy="{self.fy}" '
        if self.fr is not None or self.fr != 0:
            fill_attr += f'fr="{self.fr}" '
        fill_attr += '>\n'
        for stop in self.stops:
            fill_attr += stop.to_str()
        fill_attr += '</radialGradient>\n'
        return fill_attr

    def to_tensor(self, PAD_VAL=-1, *args, **kwargs):
        """ return torch.tensor([[cx, cy, r, fx, fy], [*self.stops[i].to_tensor() for i in range(len(self.stops))]]) """
        # stops_tensor = torch.stack([stop.to_tensor() for stop in self.stops], dim=0)
        # if len(stops_tensor) == 0:
        #     stops_tensor = torch.tensor([[PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL]], dtype=torch.float32)
        # center_tensor = torch.tensor([self.cx, self.cy], dtype=torch.float32)
        return 
    
    @staticmethod
    def from_direction(origin, direction):
        # 使わない方が無難
        fx, fy, fr = origin
        cx, cy, r = direction
        return cx, cy, r, fx, fy, fr

    @staticmethod
    def from_xml(x: minidom.Element, rules_dict=None, *args, **kwargs):
        id_name = x.getAttribute("id")
        cx = persentage_to_float(x.getAttribute("cx"), default=0.5)
        cy = persentage_to_float(x.getAttribute("cy"), default=0.5)
        r = persentage_to_float(x.getAttribute("r"), default=1.0)
        fx = persentage_to_float(x.getAttribute("fx"), default=cx)
        fy = persentage_to_float(x.getAttribute("fy"), default=cy)
        fr = persentage_to_float(x.getAttribute("fr"), default=0.0)

        stops = []
        for stop_elem in x.getElementsByTagName("stop"):
            stops.append(Stop.from_xml(stop_elem, rules_dict=rules_dict))

        return SVGRadialGradient(id_name, cx, cy, r, fx, fy, fr, stops)
