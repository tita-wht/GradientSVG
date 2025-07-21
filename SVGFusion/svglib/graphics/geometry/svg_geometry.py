# 幾何学形状をもつ要素の抽象クラス
# SVGの基本的な図形を表現するクラス群
# NOTE: あとで文字クラスの抽象クラスとして使用する可能性に気を付ける

from __future__ import annotations
from ...geom import *
from ...color import Color
from xml.dom import minidom


class SVGGeometry:
    """
    Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Basic_Shapes
    """
    def __init__(self, fill="black", stroke=None, stroke_width=".3", fill_opacity=None, stroke_opacity=None):
        # if None -> color is (-1,-1,-1,-1) , where -1 is padding value
        if isinstance(fill, Color):
            self.fill = fill
        else:
            self.fill = Color(fill, fill_opacity) if fill is not None else None # NOTE: fillに文字解析
        if isinstance(stroke, Color):
            self.storke = stroke
        else:
            self.stroke = Color(stroke, stroke_opacity) if stroke is not None else None
        self.stroke_width = stroke_width
        # NOTE: fill/stroke を使用するフラグを出力するべき？
        
        # self.all_attrs = None  # 要素の全属性(xml読み込みの場合のみ)

    def _get_color_text(self):
        fill_attr = ""
        if self.fill:
            fill_attr += f'fill="{self.fill.to_str()}" '
        if self.stroke:
            fill_attr += f'stroke="{self.stroke.to_str()}" stroke-width="{self.stroke_width}" '
        return fill_attr

    @staticmethod
    def from_xml(x: minidom.Element):
        raise NotImplementedError("This method should be implemented in subclasses")

    @staticmethod
    def from_xml_color_attrs(x: minidom.Element):
        color_attrs = {}
        color_attrs["fill"] = x.getAttribute("fill") if x.hasAttribute("fill") else "black"
        color_attrs["stroke"] = x.getAttribute("stroke") if x.hasAttribute("stroke") else None
        color_attrs["stroke_width"] = x.getAttribute("stroke-width") if x.hasAttribute("stroke-width") else ".3" # NOTE
        color_attrs["fill_opacity"] = x.getAttribute("fill-opacity") if x.hasAttribute("fill-opacity") else "1.0" 
        color_attrs["stroke_opacity"] = x.getAttribute("stroke-opacity") if x.hasAttribute("stroke-opacity") else "1.0"
        return color_attrs
    
    def get_color_attrs(self):
        """SVG要素の色に関する属性を辞書として返す"""
        return {
            "fill": self.fill,
            "stroke": self.stroke,
            "stroke_width": self.stroke_width,
        }

    # @staticmethod
    # def get_all_attrs(x: minidom.Element) -> dict:
    #     """SVG要素の全属性を辞書として返す"""
    #     d = {attr.name: attr.value for attr in x.attributes.values()}
    #     return d

    def draw(self, viewbox=Bbox(24), *args, **kwargs):
        from ...svg import SVG
        return SVG([self], viewbox=viewbox).draw(*args, **kwargs)

    def _get_viz_elements(self, with_points=False, with_handles=False, with_bboxes=False, color_firstlast=True, with_moves=True):
        return []

    def to_path(self):
        raise NotImplementedError
    
    def to_tensor(self, *args, **kwargs):
        raise NotImplementedError

    def to_color_tensor(self, PAD_VAL=-1, *args, **kwargs):
        fill_tensor = self.fill.to_tensor() if self.fill is not None else torch.tensor([PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL], dtype=torch.float32)
        stroke_tensor = self.stroke.to_tensor() if self.stroke is not None else torch.tensor([PAD_VAL, PAD_VAL, PAD_VAL, PAD_VAL], dtype=torch.float32)
                      
        return fill_tensor, stroke_tensor

    def copy(self):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError

    def fill_(self, fill="blue"):
        self.fill = Color(fill)
        self.stroke = None
        return self
