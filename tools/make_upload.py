# -*- coding: utf-8 -*-
"""生成「上传版」文件夹：只含 git 跟踪的文件，保证没有二进制。

用途：GitHub 网页上传**不认 .gitignore**，拖什么传什么。
所以上传前用这个脚本生成一份干净副本，避免把游戏数据拖进去。

用法：
    python tools/make_upload.py                 # 输出到 <仓库>-upload
    python tools/make_upload.py --out D:\\x     # 指定目录
    python tools/make_upload.py --check         # 只检查，不复制
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 允许的文件类型（其余一律视为可疑）
OK_EXT = {'.py', '.md', '.json', '.csv', '.txt', '.yml', '.yaml', '.cfg',
          '.toml', '.gitignore', '.gitattributes', '.png', '.jpg', ''}


def tracked():
    out = subprocess.run(['git', 'ls-files'], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        print('git ls-files 失败：', out.stderr.strip())
        sys.exit(1)
    return [f for f in out.stdout.splitlines() if f.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=ROOT + '-upload')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    files = tracked()
    print('git 跟踪的文件:', len(files))

    bad = []
    for f in files:
        e = os.path.splitext(f)[1].lower()
        if e not in OK_EXT:
            bad.append(f)
    if bad:
        print('\n！以下文件类型可疑（可能是数据或驱动本体）:')
        for f in bad[:20]:
            print('   ', f)
        print('   共 %d 个。请检查 .gitignore。' % len(bad))
        if a.check:
            return
    else:
        print('文件类型检查通过：没有可疑的二进制')

    if a.check:
        total = sum(os.path.getsize(os.path.join(ROOT, f))
                    for f in files if os.path.exists(os.path.join(ROOT, f)))
        print('合计 %.0f KB' % (total / 1024))
        return

    if os.path.exists(a.out):
        shutil.rmtree(a.out)
    for f in files:
        src = os.path.join(ROOT, f)
        if not os.path.exists(src):
            continue
        dst = os.path.join(a.out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    total = sum(os.path.getsize(os.path.join(a.out, f))
                for f in files if os.path.exists(os.path.join(a.out, f)))
    print('\n复制完成:', a.out)
    print('文件数 %d   合计 %.0f KB' % (len(files), total / 1024))

    # 结构概览
    from collections import Counter
    c = Counter(f.split('/')[0] for f in files)
    print('\n目录分布:')
    for k, v in c.most_common():
        print('   %-16s %d' % (k, v))


if __name__ == '__main__':
    main()
