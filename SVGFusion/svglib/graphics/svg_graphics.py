# 幾何学形状をもつ要素の抽象クラス
# SVGの基本的な図形を表現するクラス群

from __future__ import annotations
from .geom import *
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


class SVGPrimitive:
    """
    Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Basic_Shapes
    """
    def __init__(self, color="black", fill=False, dasharray=None, stroke_width=".3", opacity=1.0):
        self.color = color
        self.dasharray = dasharray
        self.stroke_width = stroke_width
        self.opacity = opacity

        self.fill = fill

    def _get_fill_attr(self):
        fill_attr = f'fill="{self.color}" fill-opacity="{self.opacity}"' if self.fill else f'fill="none" stroke="{self.color}" stroke-width="{self.stroke_width}" stroke-opacity="{self.opacity}"'
        if self.dasharray is not None and not self.fill:
            fill_attr += f' stroke-dasharray="{self.dasharray}"'
        return fill_attr

    @classmethod
    def from_xml(cls, x: minidom.Element):
        raise NotImplementedError

    def draw(self, viewbox=Bbox(24), *args, **kwargs):
        from .svg import SVG
        return SVG([self], viewbox=viewbox).draw(*args, **kwargs)

    def _get_viz_elements(self, with_points=False, with_handles=False, with_bboxes=False, color_firstlast=True, with_moves=True):
        return []

    def to_path(self):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError

    def fill_(self, fill=True):
        self.fill = fill
        return self
