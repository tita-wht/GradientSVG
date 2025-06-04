# 幾何学形状をもつ要素の抽象クラス
# SVGの基本的な図形を表現するクラス群
# NOTE: あとで文字クラスの抽象クラスとして使用する可能性に気を付ける

from __future__ import annotations
from ...geom import *
from xml.dom import minidom


class SVGGeometry:
    """
    Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Basic_Shapes
    """
    def __init__(self, fill="black", stroke=None, stroke_width=".3", fill_opacity=1.0, stroke_opacity=1.0):
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke
        self.stroke_opacity = stroke_opacity
        self.stroke_width = stroke_width
        
        # self.all_attrs = None  # 要素の全属性(xml読み込みの場合のみ)

    def _get_color_attr(self):
        fill_attr = ""
        if self.fill is not None:
            fill_attr += f'fill="{self.fill}" fill-opacity="{self.fill_opacity}" '
        if self.stroke is not None:
            fill_attr += f'stroke="{self.stroke}" stroke-width="{self.stroke_width}" stroke-opacity="{self.stroke_opacity}" '
        return fill_attr

    @staticmethod
    def from_xml(x: minidom.Element):
        raise NotImplementedError("This method should be implemented in subclasses")

    @staticmethod
    def from_xml_color_attrs(x: minidom.Element):
        color_attrs = {}
        color_attrs["fill"] = x.getAttribute("fill") if x.hasAttribute("fill") else "black"
        color_attrs["stroke"] = x.getAttribute("stroke") if x.hasAttribute("stroke") else None
        color_attrs["stroke_width"] = x.getAttribute("stroke-width") if x.hasAttribute("stroke-width") else ".3"
        color_attrs["fill_opacity"] = x.getAttribute("fill-opacity") if x.hasAttribute("fill-opacity") else "1.0" 
        color_attrs["stroke_opacity"] = x.getAttribute("stroke-opacity") if x.hasAttribute("stroke-opacity") else "1.0"
        return color_attrs
    

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

    def copy(self):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError

    def fill_(self, fill="blue"):
        self.fill = fill
        self.stroke = None
        return self
