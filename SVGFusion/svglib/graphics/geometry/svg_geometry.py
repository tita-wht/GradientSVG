# 幾何学形状をもつ要素の抽象クラス
# SVGの基本的な図形を表現するクラス群
# NOTE: あとで文字クラスの抽象クラスとして使用する可能性に気を付ける

from __future__ import annotations
from ...geom import *
from ...color import Color
from ...gradient import SVGGradient, SVGLinearGradient
from xml.dom import minidom

# colorの中にgradientを指す何らかを実装するべき。
# あるいはgradient自体がcolorの継承になるなど。

class SVGGeometry:
    # ATTRS = ["id", "class", "style", "transform"]
    ATTRS = ["fill", "stroke", "stroke-width", "fill-opacity", "stroke-opacity"]
    """
    Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Basic_Shapes
    """
    def __init__(self, fill="black", stroke=None, stroke_width=.3, fill_opacity=None, stroke_opacity=None, id=None, *args, **kwargs):
        # if None -> color is (-1,-1,-1,-1) , where -1 is padding value
        self.fill = None
        if isinstance(fill, Color):
            self.fill = fill
        elif isinstance(fill, str) and (fill.startswith("url(") and fill.endswith(")")):
            self.fill = fill[5:-1].strip() # NOTE: string
        else:
            self.fill = Color(fill, fill_opacity) if fill is not None else None
        
        self.stroke = None
        if isinstance(stroke, Color) or isinstance(stroke, SVGGradient):
            self.storke = stroke
        elif isinstance(stroke, str) and (stroke.startswith("url(") and stroke.endswith(")")):
            self.stroke = stroke[5:-1].strip() #NOTE: string
        else:
            self.stroke = Color(stroke, stroke_opacity) if stroke is not None else None
        self.stroke_width = stroke_width
        # NOTE: fill/stroke を使用するフラグを出力するべき？

        if id:
            self.id = id
            self.ATTRS.append("id")
            self.style_from_id(kwargs.get("rules_dict", {}), id)
        
        # self.all_attrs = None  # 要素の全属性(xml読み込みの場合のみ)

    def _get_color_text(self):
        fill_attr = ""
        if self.fill:
            if isinstance(self.fill, Color):
                fill_attr += f'fill="{self.fill.to_str()}" '
            elif isinstance(self.fill, str):
                fill_attr += f'fill="url(#{self.fill})" '
        if self.stroke:
            if isinstance(self.stroke, Color):
                fill_attr += f'stroke="{self.stroke.to_str()}" '
            elif isinstance(self.stroke, str):
                fill_attr += f'stroke="url(#{self.stroke.id})" '
            fill_attr += f'stroke-width="{self.stroke_width}" '
        return fill_attr

    @staticmethod
    def from_xml(x: minidom.Element, *args, **kwargs):
        raise NotImplementedError("This method should be implemented in subclasses")

    @staticmethod
    def from_xml_color_attrs(x: minidom.Element, *args, **kwargs):
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

    def style_from_id(self, rules_dict:dict, id_name: str):
        # 自身のid属性の値と一致するidセレクタを<style>中から探し、定義された属性をインスタンスに適用する。
        if not id_name.startswith("#"):
            id_name = "#" + id_name
        if id_name in rules_dict:
            print("do")
            for attr, value in rules_dict[id_name].items():
                if hasattr(self, attr):
                    setattr(self, attr, value)
                else:
                    setattr(self, attr, value)
        return self
