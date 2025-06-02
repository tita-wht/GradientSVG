# 幾何学形状をもつ要素の抽象クラス
# SVGの基本的な図形を表現するクラス群

from __future__ import annotations
from ...geom import *
import torch
import re
from typing import List, Union
from xml.dom import minidom
from .svg_path import SVGPath
from .svg_command import SVGCommandLine, SVGCommandArc, SVGCommandBezier, SVGCommandClose
import shapely
import shapely.ops
import shapely.geometry
import networkx as nx



FLOAT_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")


def extract_args(args):
    return list(map(float, FLOAT_RE.findall(args)))


class SVGGeometry:
    """
    Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Basic_Shapes
    """
    def __init__(self, fill="black", stroke=None, stroke_width=".3", fill_opacity=1.0, stroke_opacity=1.0, *args, **kwargs):
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke
        self.stroke_opacity = stroke_opacity
        self.stroke_width = stroke_width
        
        # self.all_attrs = None  # 要素の全属性(xml読み込みの場合のみ)

    def _get_fill_attr(self):
        fill_attr = ""
        if self.fill is not None:
            fill_attr += f'fill="{self.fill}" fill-opacity="{self.fill_opacity}" '
        if self.stroke is not None:
            fill_attr += f'stroke="{self.stroke}" stroke-width="{self.stroke_width}" stroke-opacity="{self.stroke_opacity}" '
        return fill_attr

    @classmethod
    def from_xml(cls, x: minidom.Element):
        raise NotImplementedError
    
    @staticmethod
    def get_all_attrs(x: minidom.Element) -> dict:
        """SVG要素の全属性を辞書として返す"""
        return {attr.name: attr.value for attr in x.attributes.values()}

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
