import os
import re

H = r'D:\GamedataUnpack\hoot20251231'
xml = open(os.path.join(H, 'xml', 'leaf.xml'), encoding='utf-8').read()

for b in re.split(r'<game>', xml):
    nm = re.search(r'<name>([^<]+)</name>', b)
    if not nm:
        continue
    roms = re.findall(r'<rom type="file"[^>]*>([^<]+)</rom>', b)
    drivers = [r for r in roms if re.match(r'(?i).*(drv|pmd|mmdr|\.com|\.exe)', r)]
    data = [r for r in roms if re.search(r'(?i)\.(md|fm|m2)$', r)]
    print('【%s】' % nm.group(1))
    print('   驱动:', ', '.join(sorted(set(drivers))) or '(无)')
    print('   数据: %d 个, 例: %s' % (
        len(data), ', '.join(sorted(set(data))[:6]) or '(无)'))
    print()
