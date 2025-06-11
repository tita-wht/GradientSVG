# FIXME:

class SVGGroup(SVGGeometry):
    def __init__(self, primitives: List[SVGPath] = None, origin=None, *args, **kwargs):
        """
        SVGGeometryを継承するプリミティブ要素をグループ化する。
        座標変換・色などの要素は<g>以下の子要素に継承される
        """
        super().__init__(*args, **kwargs)
        self.primitives = primitives

        if origin is None:
            origin = Point(0.)
        self.origin = origin

    # Alias
    @property
    def paths(self):
        return self.primitives

    @property
    def path(self):
        return self.primitives[0]

    def __getitem__(self, idx):
        return self.primitives[idx]

    def __len__(self):
        return len(self.paths)

    def total_len(self):
        return sum([len(path) for path in self.primitives])

    @property
    def start_pos(self):
        return self.primitives[0].start_pos

    @property
    def end_pos(self):
        last_path = self.primitives[-1]
        if last_path.closed:
            return last_path.start_pos
        return last_path.end_pos

    def set_origin(self, origin: Point):
        self.origin = origin
        if self.primitives:
            self.primitives[0].origin = origin
        self.recompute_origins()

    def append(self, path: SVGPath):
        self.primitives.append(path)

    def copy(self):
        return SVGPathGroup([primitive.copy() for primitive in self.primitives], self.origin.copy(),
                            self.color, self.fill, self.dasharray, self.stroke_width, self.opacity)

    def __repr__(self):
        return "SVGPathGroup({})".format(", ".join(prim.__repr__() for prim in self.primitives))

    def _get_viz_elements(self, with_points=False, with_handles=False, with_bboxes=False, color_firstlast=True, with_moves=True):
        viz_elements = []
        for prim in self.primitievs:
            viz_elements.extend(prim._get_viz_elements(with_points, with_handles, with_bboxes, color_firstlast, with_moves))

        if with_bboxes:
            viz_elements.append(self._get_bbox_viz())

        return viz_elements

    def _get_bbox_viz(self):
        color = "red" if self.color == "black" else self.color
        bbox = self.bbox().to_rectangle(color=color)
        return bbox

    def to_path(self):
        return self

    def to_str(self, with_markers=False, *args, **kwargs):
        color_attr = self._get_color_attr()
        marker_attr = 'marker-start="url(#arrow)"' if with_markers else ''
        return '<path {} {} filling="{}" d="{}"></path>'.format(color_attr, marker_attr, self.path.filling, " ".join(prim.to_str() for prim in self.primitives))

    def to_tensor(self, PAD_VAL=-1):
        return torch.cat([p.to_tensor(PAD_VAL=PAD_VAL) for p in self.primitives], dim=0)

    def _apply_to_paths(self, method, *args, **kwargs):
        for path in self.primitives:
            getattr(path, method)(*args, **kwargs)
        return self

    def translate(self, vec):
        return self._apply_to_paths("translate", vec)

    def rotate(self, angle: Angle):
        return self._apply_to_paths("rotate", angle)

    def scale(self, factor):
        return self._apply_to_paths("scale", factor)

    def numericalize(self, n=256):
        return self._apply_to_paths("numericalize", n)

    def drop_z(self):
        return self._apply_to_paths("set_closed", False)

    def recompute_origins(self):
        origin = self.origin
        for prim in self.primitives:
            prim.origin = origin.copy()
            origin = prim.end_pos
        return self

    def reorder(self):
        self._apply_to_paths("reorder")
        self.recompute_origins()
        return self

    def filter_empty(self):
        # FIXME
        # コマンドがないpathを除去するフィルター
        # paths -> primitives に変えたので、空のpath以外も対応させたい
        self.primitives = [prim for prim in self.primitives if prim.path_commands]
        return self

    def canonicalize(self):
        # NOTE & FIXME: paths時代の名残。始点によってプリミティブの順序を入れ替えてるだけなので残しておいても問題ないはず…？ 参照も見当たらない

        # パスの正規化を行う
        # パスの視点の座標値(y,xの順)でソート
        # パスの向きを時計回りに並び明け（reverse)
        # ↑ 後に始点を再計算
        self.primitives = sorted(self.primitives, key=lambda x: x.start_pos.tolist()[::-1])
        if not self.primitives[0].is_clockwise():
            self._apply_to_paths("reverse")

        self.recompute_origins()
        return self

    def reverse(self):
        self._apply_to_paths("reverse")

        self.recompute_origins()
        return self

    def duplicate_extremities(self):
        self._apply_to_paths("duplicate_extremities")
        return self

    def reverse_non_closed(self):
        self._apply_to_paths("reverse_non_closed")

        self.recompute_origins()
        return self

    def simplify(self, tolerance=0.1, epsilon=0.1, angle_threshold=179., force_smooth=False):
        self._apply_to_paths("simplify", tolerance=tolerance, epsilon=epsilon, angle_threshold=angle_threshold,
                             force_smooth=force_smooth)
        self.recompute_origins()
        return self

    def split_paths(self):
        return [SVGPathGroup([prim], self.origin,
                             self.color, self.fill, self.dasharray, self.stroke_width, self.opacity)
                for prim in self.primitives]

    def split(self, n=None, max_dist=None, include_lines=True):
        return self._apply_to_paths("split", n=n, max_dist=max_dist, include_lines=include_lines)

    def simplify_arcs(self):
        return self._apply_to_paths("simplify_arcs")

    def filter_consecutives(self):
        return self._apply_to_paths("filter_consecutives")

    def filter_duplicates(self):
        return self._apply_to_paths("filter_duplicates")

    def bbox(self):
        return union_bbox([prim.bbox() for prim in self.primitives])

    def to_shapely(self):
        return shapely.ops.unary_union([prim.to_shapely() for prim in self.primitives])

    def compute_filling(self):
        if self.fill:
            G = self.overlap_graph()

            root_nodes = [i for i, d in G.in_degree() if d == 0]

            for root in root_nodes:
                if not self.primitives[root].closed:
                    continue

                current = [(1, root)]

                while current:
                    visited = set()
                    neighbors = set()
                    for d, n in current:
                        self.primitives[n].set_filling(d != 0)

                        for n2 in G.neighbors(n):
                            if not n2 in visited:
                                d2 = d + (self.primitives[n2].is_clockwise() == self.primitives[n].is_clockwise()) * 2 - 1
                                visited.add(n2)
                                neighbors.add((d2, n2))

                    G.remove_nodes_from([n for d, n in current])

                    current = [(d, n) for d, n in neighbors if G.in_degree(n) == 0]

        return self

    def overlap_graph(self, threshold=0.9, draw=False):
        G = nx.DiGraph()
        shapes = [prim.to_shapely() for prim in self.primitives]

        for i, path1 in enumerate(shapes):
            G.add_node(i)

            if self.primitives[i].closed:
                for j, path2 in enumerate(shapes):
                    if i != j and self.primitives[j].closed:
                        overlap = path1.intersection(path2).area / path1.area
                        if overlap > threshold:
                            G.add_edge(j, i, weight=overlap)

        if draw:
            pos = nx.spring_layout(G)
            nx.draw_networkx(G, pos, with_labels=True)
            labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
        return G

    def bbox_overlap(self, other: SVGPathGroup):
        return self.bbox().overlap(other.bbox())

    def to_points(self):
        return np.concatenate([prim.to_points() for prim in self.primitives])
