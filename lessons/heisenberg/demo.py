# -*- coding: utf-8 -*-
"""最小海森堡模型：观测方式改变被观测对象的行为。

不依赖 Unicorn / 不依赖 PC-98。
只演示一件事：一条 lazy-flags 的比较链，被"探头"在错误的位置实体化之后，
分支结果会翻转 —— 而两次运行喂进去的输入完全相同。
"""


class LazyCPU:
    """不保存 EFLAGS，只保存 (op, a, b)，需要时才现算 —— 模拟 TCG 的懒标志位。"""

    def __init__(self):
        self.cc = None          # ('cmp', a, b)
        self.flags = None       # 实体化之后的真实标志位
        self.log = []

    # ---- 运算 ----
    def cmp(self, a, b):
        self.cc = ('cmp', a, b)     # 注意：不算标志位
        self.flags = None
        self.log.append('cmp %d,%d' % (a, b))

    def materialize(self):
        """把懒标志位实体化 —— 这就是 code hook 做的事。

        真实的 QEMU/Unicorn 在这里会用「上一次已实体化的 EFLAGS」来重建，
        而不是重算。链一旦被切断，快照就是**陈旧的**（这里是全 0）。
        """
        if self.cc is None:
            return                      # 链还没建立：打断无害
        self.flags = {'zf': False, 'cf': False}   # 陈旧快照（真实是全 0）
        self.cc = None

    def zf(self):
        if self.flags is not None:          # 已被实体化 → 只能用快照
            return self.flags['zf']
        if self.cc is None:
            return False
        op, a, b = self.cc                  # 现算
        return a == b


def run(probe_at=None, verbose=True):
    """执行一段小程序；probe_at 指定在哪条指令前插入探头。"""
    cpu = LazyCPU()
    out = []
    program = [
        ('load', 3),        # 0: 取一个值（放在寄存器里）
        ('cmp', 3),         # 1: 与 3 比较
        ('je_double',),     # 2: 相等就翻倍
        ('jmp_end',),       # 3
        ('double',),        # 4
        ('end',),           # 5
    ]
    val = 0
    pc = 0
    for _ in range(16):
        if probe_at is not None and pc == probe_at:
            cpu.materialize()           # ← 探头：强制把懒标志位写成真值
            if verbose:
                out.append('  [probe @%d] flags=%s' % (pc, cpu.flags))
        ins = program[pc]
        op = ins[0]
        if op == 'load':
            val = ins[1]
            cpu.log.append('load %d' % val)
            pc += 1
        elif op == 'cmp':
            cpu.cmp(val, ins[1])
            pc += 1
        elif op == 'je_double':
            if cpu.zf():                # ← 这里读 ZF
                pc = 4
            else:
                pc += 1
        elif op == 'jmp_end':
            pc = 5
        elif op == 'double':
            val *= 2
            out.append('double -> %d' % val)
            pc = 5
        elif op == 'end':
            out.append('result = %d' % val)
            break
    return val, out


def main():
    print('同一个程序、同一份输入（val=3, 与 3 比较），只改"观测方式"：\n')
    for label, probe in (('无探头', None),
                         ('探头插在 cmp 之后、je 之前', 2),
                         ('探头插在 cmp 之前', 1)):
        val, out = run(probe_at=probe)
        print('【%s】' % label)
        for line in out:
            print('   ', line)
        print('   => 结果 %d\n' % val)
    print('对照：')
    print('  无探头              -> 6')
    print('  探头在 cmp/je 之间  -> 3   （je 用了错误的标志位快照）')
    print('  探头在 cmp 之前      -> 6   （链还没建立，打断无害）')
    print('\n结论：输出不是 f(输入)，是 f(输入, 怎么观测)。')
    print('      探头插错位置，会造出一个"稳定但错误"的世界。')


if __name__ == '__main__':
    main()
