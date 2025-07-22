
def persentage_to_px(persentage_str, length):
    """ NOTE: SVGの長さ指定について。
    例えば x=10 とした場合、これは10pxを意味する（絶対座標）
    しかし、x=10% とした場合、これはviewbox（適用される上位要素）の幅の10%を意味する（相対座標）
    絶対座標は色々あるが、数字 px, cm, mm, in, pt, pc で指定される。
    相対座標は数字 %, em, exで指定される。

    結論を言うと、しゃらくさいので px と % だけ考慮すべき。
    """
    if persentage_str.endswith('%'):
        return float(persentage_str[:-1]) / 100.0 * length
    else:
        return float(persentage_str) * length

def persentage_to_float(persentage_str, default=1.0):
    if persentage_str.endswith('%'):
        ret = float(persentage_str[:-1]) / 100.0
    elif persentage_str == "":
        ret = default
    else: # 0.0~1.0
        ret = float(persentage_str)
    return ret

def get_rule(rules_dict, name, selector_type='class'):
    if selector_type == 'class' or selector_type == '.':
        if not name.startswith('.'):
            name = '.' + name
    elif selector_type == 'id' or selector_type == '#':
        if not name.startswith('#'):
            name = '#' + name
    return rules_dict.get(name, {})
