# -*- coding: utf-8 -*-
"""把 HOOT pc98 库里本地没有的包全部下载下来。

用法：
    python hoot_download.py            # 只显示计划
    python hoot_download.py --go       # 真的下载
    python hoot_download.py --go --jobs 8
"""
import argparse
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

INDEX = r'D:\gf\pc98-midi-drivers\build\hoot_index.html'
DEST = r'D:\GamedataUnpack\hoot20251231\pc98'
BASE = 'https://hoot.joshw.info/pc98/'
UNIT = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}


def load_plan():
    t = open(INDEX, encoding='utf-8', errors='replace').read()
    rows = []
    for m in re.finditer(
            r'href="([^"]+\.zip)"[^>]*>[^<]*</a>\s*[\d-]+\s+[\d:]+\s*([\d.]+)\s*([KMG]?)',
            t, re.I):
        rows.append((urllib.parse.unquote(m.group(1)), float(m.group(2)) * UNIT.get(m.group(3).upper() or 'B', 1)))
    local = {f[:-4].lower() for f in os.listdir(DEST) if f.lower().endswith('.zip')}
    return [(n, s) for n, s in rows if n[:-4].lower() not in local]


def fetch(name, retries=3):
    url = BASE + urllib.parse.quote(name)
    dst = os.path.join(DEST, name)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'hoot-fetch/1.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 22 or data[:2] != b'PK':
                raise IOError('不是 zip（%d 字节）' % len(data))
            tmp = dst + '.part'
            open(tmp, 'wb').write(data)
            os.replace(tmp, dst)
            return name, len(data), None
        except Exception as e:
            if i == retries - 1:
                return name, 0, str(e)
            time.sleep(1.5 * (i + 1))
    return name, 0, '未知错误'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--go', action='store_true', help='真的下载')
    ap.add_argument('--jobs', type=int, default=6)
    a = ap.parse_args()

    plan = load_plan()
    total = sum(s for _, s in plan)
    print('待下载 %d 个，合计 %.1f MB' % (len(plan), total / 1024 / 1024))
    if not a.go:
        for n, s in plan[:10]:
            print('   %-26s %8.1f KB' % (n, s / 1024))
        print('   ...')
        print('加 --go 开始下载')
        return

    os.makedirs(DEST, exist_ok=True)
    done = fail = 0
    got = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(fetch, n): n for n, _ in plan}
        for f in as_completed(futs):
            name, size, err = f.result()
            if err:
                fail += 1
                print('  ✗ %-24s %s' % (name, err))
            else:
                done += 1
                got += size
            if (done + fail) % 100 == 0:
                el = time.time() - t0
                print('  进度 %d/%d  %.1f MB  %.0f 秒'
                      % (done + fail, len(plan), got / 1024 / 1024, el))
    print('\n完成 %d 个，失败 %d 个，共 %.1f MB，用时 %.0f 秒'
          % (done, fail, got / 1024 / 1024, time.time() - t0))


if __name__ == '__main__':
    main()
