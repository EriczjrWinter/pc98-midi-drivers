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
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 允许的文件类型（其余一律视为可疑）
OK_EXT = {'.py', '.md', '.json', '.csv', '.txt', '.yml', '.yaml', '.cfg',
          '.toml', '.gitignore', '.gitattributes', '.png', '.jpg'}

# 上传时排除的文件（只在本地维护，不适合公开）
# - docs/NEXT.md / HANDOFF.md：给下一个会话看的交接文档，时效性强，且含会话协作细节
# - docs/PIPELINE.md：含“运营协议 / 开会话省钱”这类内部工作流程
SKIP = {
    'docs/NEXT.md',
    'docs/HANDOFF.md',
    'docs/PIPELINE.md',
    'docs/REVIEW-CHECKLIST.md',
    'build/mdt/HANDOFF.md',
}

# 内部用语：上传版里不该出现（出现就人工清理）
INTERNAL = re.compile(r'本会话|下一个会话|另一个会话|这次会话|开会话|烧了|这笔钱')


def tracked():
    out = subprocess.run(['git', 'ls-files'], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        print('git ls-files 失败：', out.stderr.strip())
        sys.exit(1)
    return [f for f in out.stdout.splitlines() if f.strip()]


def untracked():
    """未跟踪但不该被忽略的文件——它们不会进上传版，要单独提醒。"""
    out = subprocess.run(['git', 'ls-files', '--others',
                          '--exclude-standard'], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return []
    return [f for f in out.stdout.splitlines() if f.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=ROOT + '-upload')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    files = tracked()
    skipped = [f for f in files if f in SKIP]
    files = [f for f in files if f not in SKIP]
    print('git 跟踪的文件:', len(tracked()))
    if skipped:
        print('按 SKIP 排除:', ', '.join(skipped))
    print('实际导出:', len(files))

    # 未跟踪的源码/文档不会进上传版——这是最容易「漏东西」的地方
    loose = [f for f in untracked()
             if os.path.splitext(f)[1].lower() in ('.py', '.md', '.json', '.txt')]
    if loose:
        print('\n！以下文件未跟踪，不会进上传版（先 git add）:')
        for f in loose[:20]:
            print('   ', f)
        print('   共 %d 个。' % len(loose))

    bad = []
    bare = []
    for f in files:
        base = os.path.basename(f)
        e = base.lower() if base.startswith('.') else os.path.splitext(base)[1].lower()
        if not e:
            bare.append(f)          # 无扩展名的文件：只提示，不拦
        elif e not in OK_EXT:
            bad.append(f)
    # 内部用语扫描（只对将要上传的文本文件）
    hits = []
    for f in files:
        if f == 'tools/make_upload.py':
            continue
        if not f.lower().endswith(('.md', '.txt', '.py', '.csv')):
            continue
        try:
            t = open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore').read()
        except Exception:                                   # noqa: BLE001
            continue
        for m in INTERNAL.finditer(t):
            line = t[:m.start()].count('\n') + 1
            hits.append((f, line, m.group(0)))
    if hits:
        print('\n！上传版里出现内部用语（建议改写，或把整份文件加入 SKIP）:')
        for f, line, word in hits[:20]:
            print('   %s:%d  %s' % (f, line, word))
        print('   共 %d 处。' % len(hits))

    if bare:
        print('\n无扩展名的跟踪文件（确认不是驱动本体）:')
        for f in bare:
            print('   ', f)
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
