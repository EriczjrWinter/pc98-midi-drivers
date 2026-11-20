# -*- coding: utf-8 -*-
"""保底导出：把所有 MIDI 作品的文件原样解出来，按会社/作品归档。

即使驱动暂时解不开，数据也不会丢。

用法：
    python dump_all.py            # 看计划
    python dump_all.py --go       # 真的解
    python dump_all.py --go --max-files 8    # 只处理文件数 <= 8 的小包（先啃小虾米）
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import zipfile

X = r'D:\GamedataUnpack\hoot20251231\xml'
PC98 = r'D:\GamedataUnpack\hoot20251231\pc98'
OUT = r'D:\gf\pc98-midi-drivers\dump'
MANIFEST = r'D:\gf\pc98-midi-drivers\build\dump_manifest.json'


def collect():
    """返回 {archive: {name, company}}，只含 midiout=1 的作品。"""
    packs = {}
    for fn in sorted(os.listdir(X)):
        if not fn.endswith('.xml'):
            continue
        company = fn[:-4]
        t = open(os.path.join(X, fn), encoding='utf-8', errors='replace').read()
        for b in re.split(r'<game>', t):
            a = re.search(r'archive="([^"]+)"', b)
            nm = re.search(r'<name>([^<]+)</name>', b)
            if not a or not nm:
                continue
            if not re.search(r'name="midiout"\s+value="1"', b):
                continue
            packs.setdefault(a.group(1), {'name': nm.group(1),
                                           'company': company})
    return packs


def safe(s):
    for c in '\\/:*?"<>|':
        s = s.replace(c, '_')
    return s.strip()[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--go', action='store_true')
    ap.add_argument('--max-files', type=int, default=0,
                    help='只处理文件数不超过 N 的包（0=不限）')
    a = ap.parse_args()

    packs = collect()
    print('MIDI 包:', len(packs))

    plan = []
    skipped_missing = 0
    rename = {}
    mp = r'D:\gf\pc98-midi-drivers\build\rename_map.json'
    if os.path.exists(mp):
        rename = json.load(open(mp, encoding='utf-8'))
    for key, ent in sorted(packs.items()):
        zp = os.path.join(PC98, key + '.zip')
        if not os.path.exists(zp) and key in rename:
            zp = os.path.join(PC98, rename[key] + '.zip')
        if not os.path.exists(zp):
            skipped_missing += 1
            continue
        try:
            z = zipfile.ZipFile(zp)
        except Exception:
            skipped_missing += 1
            continue
        files = [i for i in z.infolist() if not i.is_dir()]
        if a.max_files and len(files) > a.max_files:
            continue
        plan.append((key, ent, zp, len(files), sum(i.file_size for i in files)))

    print('可导出:', len(plan), '  找不到 zip:', skipped_missing)
    if a.max_files:
        print('（已过滤：文件数 <= %d）' % a.max_files)
    total = sum(p[4] for p in plan)
    print('合计 %.1f MB' % (total / 1024 / 1024))
    if not a.go:
        for key, ent, _, n, sz in plan[:12]:
            print('   %-20s %2d 个文件 %7.1f KB  %s'
                  % (key, n, sz / 1024, ent['name'][:34]))
        print('   ...')
        print('加 --go 开始导出')
        return

    manifest = []
    done = 0
    for key, ent, zp, n, sz in plan:
        d = os.path.join(OUT, safe(ent['company']), safe(key))
        os.makedirs(d, exist_ok=True)
        z = zipfile.ZipFile(zp)
        info = {'archive': key, 'name': ent['name'], 'company': ent['company'],
                'files': [], 'driver': None}
        for i in z.infolist():
            if i.is_dir():
                continue
            name = os.path.basename(i.filename)
            try:
                data = z.read(i.filename)
            except Exception:
                continue
            open(os.path.join(d, safe(name)), 'wb').write(data)
            h = hashlib.md5(data).hexdigest()[:12]
            info['files'].append({'name': name, 'size': len(data), 'hash': h})
        # 主驱动：体积最大、扩展名像可执行的那个
        exe = [f for f in info['files']
               if os.path.splitext(f['name'])[1].lower()
               in ('.com', '.exe', '.drv', '.sys') and f['size'] >= 400]
        if exe:
            drv = max(exe, key=lambda x: x['size'])
            info['driver'] = {'name': drv['name'], 'size': drv['size'],
                              'hash': drv['hash']}
        manifest.append(info)
        done += 1
        if done % 50 == 0:
            print('  已导出 %d/%d' % (done, len(plan)))

    json.dump(manifest, open(MANIFEST, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n导出完成 %d 个包 → %s' % (done, OUT))
    print('清单 →', MANIFEST)


if __name__ == '__main__':
    main()
