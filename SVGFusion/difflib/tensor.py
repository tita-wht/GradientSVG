from __future__ import annotations
import torch
import torch.utils.data
from typing import Union
Num = Union[int, float]

# NOTE: パディングの値が-1の場合、SOS追加によって、SOSの次トークンの初期位置が-1になる。

class SVGTensor: 
    """論文中 S_(i,j) を示す 

    Returns:
        _type_: _description_
    """
    
    ELEMENTS = ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon",  "EOS", "SOS"]

    PATH_COMMANDS = ["m", # path moveTo
                     "l", # path lineTo 
                     "c", # path cubic bezier curve
                     "q", # path quadratic bezier curve
                     "a", # path arcTo
                     "z"] # path closePath
    
    #                              rad  x  lrg sw  ctrl ctrl  end
    #                              ius axs arc eep  1    2    pos
    #                                   rot fg fg
    CMD_ARGS_MASK = torch.tensor([[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],   # m
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],   # l
                                  [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],   # c
                                  [0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],   # q
                                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1],   # a
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])  # z

    class Index:  # indicate S_(i,j) indices (show in paper))
        ELEMENT = 0
        COMMAND = 1
        RADIUS = slice(2, 4)
        X_AXIS_ROT = 4
        LARGE_ARC_FLG = 5
        SWEEP_FLG = 6
        START_POS = slice(7, 9)
        CONTROL1 = slice(9, 11)
        CONTROL2 = slice(11, 13)
        END_POS = slice(13, 15)

    class IndexArgs: # CMD_ARGS_MASK indices 
        RADIUS = slice(0, 2)
        X_AXIS_ROT = 2          # rotated by this angle (degrees) around x-axis
        LARGE_ARC_FLG = 3
        SWEEP_FLG = 4
        CONTROL1 = slice(5, 7)  # NOTE: ctrl0 is root posisiton = start_pos
        CONTROL2 = slice(7, 9)
        END_POS = slice(9, 11)

    position_keys = ["control1", "control2", "end_pos"]
    all_position_keys = ["start_pos", *position_keys]
    arg_keys = ["radius", "x_axis_rot", "large_arc_flg", "sweep_flg", *position_keys]
    all_arg_keys = [*arg_keys[:4], "start_pos", *arg_keys[4:]]
    elem_keys = ["elements", "commands", *arg_keys]
    all_elem_keys = ["elements", "commands", *all_arg_keys]

    def __init__(self, elements, commands, radius, x_axis_rot, large_arc_flg, sweep_flg, control1, control2, end_pos, seq_len=None, label=None, PAD_VAL=-1, ARGS_DIM=256, filling=0):

        self.elements = elements.reshape(-1, 1).float()
        self.commands = commands.reshape(-1, 1).float()

        self.radius = radius.float()
        self.x_axis_rot = x_axis_rot.reshape(-1, 1).float()
        self.large_arc_flg = large_arc_flg.reshape(-1, 1).float()
        self.sweep_flg = sweep_flg.reshape(-1, 1).float()

        self.control1 = control1.float()
        self.control2 = control2.float()
        self.end_pos = end_pos.float()

        self.seq_len = torch.tensor(len(elements)) if seq_len is None else seq_len
        self.label = label

        self.PAD_VAL = PAD_VAL
        self.ARGS_DIM = ARGS_DIM

        self.sos_token = torch.Tensor([self.ELEMENTS.index("SOS")]).unsqueeze(-1)
        self.eos_token = self.pad_token = torch.Tensor([self.ELEMENTS.index("EOS")]).unsqueeze(-1)

        self.filling = filling

    @property
    def start_pos(self):
        start_pos = self.end_pos[:-1]

        return torch.cat([
            start_pos.new_zeros(1, 2),
            start_pos
        ])

    @staticmethod
    def from_data(data, *args, **kwargs):
        # sample_data = torch.tensor([
        #         [0, 0, 10, 20, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6],  # 1行目: rect
        #         [1, 1, 15, 25, 0, 0, 0, 0, 0, 5, 6, 7, 8, 9, 10], # 2行目: circle
        #         ], dtype=torch.float32)
        return SVGTensor(data[:, SVGTensor.Index.ELEMENT],
                         data[:, SVGTensor.Index.COMMAND], 
                         data[:, SVGTensor.Index.RADIUS], 
                         data[:, SVGTensor.Index.X_AXIS_ROT],
                         data[:, SVGTensor.Index.LARGE_ARC_FLG], 
                         data[:, SVGTensor.Index.SWEEP_FLG], 
                         data[:, SVGTensor.Index.CONTROL1],
                         data[:, SVGTensor.Index.CONTROL2], 
                         data[:, SVGTensor.Index.END_POS], 
                         *args, **kwargs)

    @staticmethod
    def from_cmd_args(elements, commands, args, *nargs, **kwargs): # MEMO: 呼び出し注意
        return SVGTensor(elements, 
                         commands, 
                         args[:, SVGTensor.IndexArgs.RADIUS], 
                         args[:, SVGTensor.IndexArgs.X_AXIS_ROT],
                         args[:, SVGTensor.IndexArgs.LARGE_ARC_FLG], 
                         args[:, SVGTensor.IndexArgs.SWEEP_FLG], 
                         args[:, SVGTensor.IndexArgs.CONTROL1],
                         args[:, SVGTensor.IndexArgs.CONTROL2], 
                         args[:, SVGTensor.IndexArgs.END_POS], 
                         *nargs, **kwargs)

    def get_data(self, keys):
        return torch.cat([self.__getattribute__(key) for key in keys], dim=-1)

    @property
    def data(self):
        return self.get_data(self.all_elem_keys)

    def copy(self):
        return SVGTensor(*[self.__getattribute__(key).clone() for key in self.cmd_arg_keys],
                         seq_len=self.seq_len.clone(), label=self.label, PAD_VAL=self.PAD_VAL, ARGS_DIM=self.ARGS_DIM, filling=self.filling)

    def add_sos(self): # NOTE: pad_val = -1 (in paper, PAD_VAL = 0)
        self.elements = torch.cat([self.sos_token, self.elements])
        self.commands = torch.cat([self.commands.new_full((1, 1), self.PAD_VAL), self.commands])

        for key in self.arg_keys:
            v = self.__getattribute__(key)
            self.__setattr__(key, torch.cat([v.new_full((1, v.size(-1)), self.PAD_VAL), v]))

        self.seq_len += 1
        return self

    def drop_sos(self):
        for key in self.elem_keys:
            self.__setattr__(key, self.__getattribute__(key)[1:])

        self.seq_len -= 1
        return self

    def add_eos(self):
        self.elements = torch.cat([self.elements, self.eos_token])
        self.commands = torch.cat([self.commands.new_full((1, 1), self.PAD_VAL), self.commands])

        for key in self.arg_keys:
            v = self.__getattribute__(key)
            self.__setattr__(key, torch.cat([v, v.new_full((1, v.size(-1)), self.PAD_VAL)]))

        return self

    def pad(self, seq_len=51):
        pad_len = max(seq_len - len(self.elements), 0)

        self.elements = torch.cat([self.elements, self.pad_token.repeat(pad_len, 1)])
        self.commands = torch.cat([self.commands, self.pad_token.repeat(pad_len, 1)])

        for key in self.arg_keys:
            v = self.__getattribute__(key)
            self.__setattr__(key, torch.cat([v, v.new_full((pad_len, v.size(-1)), self.PAD_VAL)]))

        return self

    def unpad(self):
        # Remove EOS + padding
        for key in self.elem_keys:
            self.__setattr__(key, self.__getattribute__(key)[:self.seq_len])
        return self

    def draw(self, *args, **kwags):
        from svglib.svg import SVGPath
        return SVGPath.from_tensor(self.data).draw(*args, **kwags)

    def elems(self):
        return self.elements.reshape(-1)
    
    def cmds(self):
        return self.commands.reshape(-1)

    def args(self, with_start_pos=False):
        if with_start_pos:
            return self.get_data(self.all_arg_keys)

        return self.get_data(self.arg_keys)

    def _get_real_commands_mask(self):
        elem_mask = self.elems() < self.ELEMENTS.index("EOS") # There are elements other than EOS and SOS
        cmd_mask = self.cmds() < len(self.PATH_COMMANDS) # There are commands other than z
        mask = elem_mask & cmd_mask
        return mask

    def _get_args_mask(self):
        mask = SVGTensor.CMD_ARGS_MASK[self.cmds().long()].bool()
        return mask

    def get_relative_args(self):
        data = self.args().clone()

        real_commands = self._get_real_commands_mask()
        data_real_commands = data[real_commands]

        start_pos = data_real_commands[:-1, SVGTensor.IndexArgs.END_POS].clone()

        data_real_commands[1:, SVGTensor.IndexArgs.CONTROL1] -= start_pos
        data_real_commands[1:, SVGTensor.IndexArgs.CONTROL2] -= start_pos
        data_real_commands[1:, SVGTensor.IndexArgs.END_POS] -= start_pos
        data[real_commands] = data_real_commands

        mask = self._get_args_mask()
        data[mask] += self.ARGS_DIM - 1
        data[~mask] = self.PAD_VAL

        return data

    def sample_points(self, n=10):
        device = self.commands.device

        z = torch.linspace(0, 1, n, device=device)
        Z = torch.stack([torch.ones_like(z), z, z.pow(2), z.pow(3)], dim=1)

        Q = torch.tensor([
            [[0., 0., 0., 0.],  #  "m"
             [0., 0., 0., 0.],
             [0., 0., 0., 0.],
             [0., 0., 0., 0.]],

            [[1., 0., 0., 0.],  # "l"
             [-1, 0., 0., 1.],
             [0., 0., 0., 0.],
             [0., 0., 0., 0.]],

            [[1., 0., 0., 0.],  #  "c"
             [-3, 3., 0., 0.],
             [3., -6, 3., 0.],
             [-1, 3., -3, 1.]],

            torch.zeros(4, 4),  # "a", no support yet

            torch.zeros(4, 4),  # "EOS"
            torch.zeros(4, 4),  # "SOS"
            torch.zeros(4, 4),  # "z"
        ], device=device)

        commands, pos = self.commands.reshape(-1).long(), self.get_data(self.all_position_keys).reshape(-1, 4, 2)
        inds = (commands == self.COMMANDS_SIMPLIFIED.index("l")) | (commands == self.COMMANDS_SIMPLIFIED.index("c"))
        commands, pos = commands[inds], pos[inds]

        Z_coeffs = torch.matmul(Q[commands], pos)

        # Last point being first point of next command, we drop last point except the one from the last command
        sample_points = torch.matmul(Z, Z_coeffs)
        sample_points = torch.cat([sample_points[:, :-1].reshape(-1, 2), sample_points[-1, -1].unsqueeze(0)])

        return sample_points

    @staticmethod
    def get_length_distribution(p, normalize=True):
        start, end = p[:-1], p[1:]
        length_distr = torch.norm(end - start, dim=-1).cumsum(dim=0)
        length_distr = torch.cat([length_distr.new_zeros(1), length_distr])
        if normalize:
            length_distr = length_distr / length_distr[-1]
        return length_distr

    def sample_uniform_points(self, n=100):
        p = self.sample_points(n=n)

        distr_unif = torch.linspace(0., 1., n).to(p.device)
        distr = self.get_length_distribution(p, normalize=True)
        d = torch.cdist(distr_unif.unsqueeze(-1), distr.unsqueeze(-1))
        matching = d.argmin(dim=-1)

        return p[matching]

