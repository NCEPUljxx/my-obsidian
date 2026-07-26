import os, re

NOTES = [
    ('MySQL-基础篇.md', '基础篇'),
    ('MySQL-进阶篇.md', '进阶篇'),
    ('MySQL-运维篇.md', '运维篇'),
]

SQL_RE = re.compile(
    r'^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|SHOW|SET|DESC|EXPLAIN|'
    r'GRANT|REVOKE|TRUNCATE|FLUSH|USE|LOAD|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|'
    r'VALUES|INTO|GLOBAL|LOCAL|INFILE|ENGINE|PRIMARY|KEY|INDEX|NULL|NOT|'
    r'AUTO_INCREMENT|BEGIN|COMMIT|ROLLBACK|CALL|DECLARE|RENAME|UNIQUE|FOREIGN|'
    r'REFERENCES|DEFAULT|CHARSET|COLLATE|CHAR|VARCHAR|INT|BIGINT|TINYINT|'
    r'DOUBLE|FLOAT|TEXT|DATE|CONSTRAINT|ADD|MODIFY|COLUMN|IF|THEN|ELSE|WHILE|'
    r'REPEAT|ORDER|GROUP|HAVING|LIMIT|UNION|RETURNS|CURSOR|FETCH|DECLARE|'
    r'MASTER|SLAVE|GRANT|REVOKE|PARTITION|TRIGGER|PROCEDURE|FUNCTION|'
    r'VIEW|COUNT|SUM|AVG|MAX|MIN|IN|LIKE|BETWEEN|EXISTS|DISTINCT|'
    r'SCHEMA|DATABASES|TABLES|STATUS|VARIABLES|ENGINES)\b', re.I)

IMG_MAP = {}
for d in ['基础篇', '进阶篇', '运维篇']:
    dp = f'D:/Java/data/MySQL/{d}'
    if os.path.isdir(dp):
        IMG_MAP[d] = set(os.listdir(dp))

for note_name, img_name in NOTES:
    fpath = os.path.join('MySQL', note_name)
    img_dir = f'D:/Java/data/MySQL/{img_name}'
    img_files = IMG_MAP.get(img_name, set())

    with open(fpath, encoding='utf-8') as f:
        raw = f.read()
    raw = raw.replace('\r\n', '\n')

    # ---- Fix image extensions ----
    def fix_img(m):
        path = m.group(1).replace(chr(92), '/')
        fn = path.rsplit('/', 1)[-1]
        stem = fn.rsplit('.', 1)[0]
        for af in img_files:
            if af.rsplit('.', 1)[0] == stem:
                return f'![]({img_dir}/{af})'
        return m.group(0)

    raw = re.sub(r'!\[\]\(([^)]+)\)', fix_img, raw)

    # ---- Remove prose from SQL blocks ----
    lines = raw.split('\n')
    out = []
    i = 0

    while i < len(lines):
        s = lines[i].strip()

        if s in ('```sql', '```'):
            fence = s
            j = i + 1
            block_in = []
            while j < len(lines) and lines[j].strip() not in ('```', '```sql'):
                block_in.append(lines[j])
                j += 1

            if j >= len(lines):
                out.append(lines[i])
                i += 1
                continue

            closing = lines[j].strip()

            code_lines = []
            prose_lines = []
            headings = []
            for bl in block_in:
                bs = bl.strip()
                if not bs:
                    code_lines.append('')
                    continue
                if bs.startswith('#'):
                    headings.append(bl)
                elif SQL_RE.match(bs):
                    code_lines.append(bl)
                elif bs.startswith('--'):
                    code_lines.append(bl)
                elif re.match(r'^\d{1,3}\s{2,}', bs):
                    code_lines.append(re.sub(r'^\d{1,3}\s{2,}', '', bl))
                elif bs.startswith('![]('):
                    prose_lines.append(bl)
                elif re.search(r'[一-鿿]', bs):
                    prose_lines.append(bl)
                elif re.match(r'^[`a-z_]+\s+(int|varchar|char|date|text|bigint|tinyint', bs, re.I):
                    code_lines.append(bl)
                elif re.match(r'^\)\s*\w', bs):
                    code_lines.append(bl)
                elif len(bs) < 3 and bs.isdigit():
                    pass
                else:
                    code_lines.append(bl)

            # Remove trailing empty lines
            while code_lines and code_lines[-1].strip() == '':
                code_lines.pop()
            while code_lines and code_lines[0].strip() == '':
                code_lines.pop(0)

            # Remove consecutive empty lines
            deduped = []
            for cl in code_lines:
                if cl.strip() == '' and deduped and deduped[-1].strip() == '':
                    continue
                deduped.append(cl)

            if deduped:
                out.append(fence)
                out.extend(deduped)
                out.append(closing)
                out.append('')

            if headings:
                out.extend(headings)
                out.append('')
            if prose_lines:
                out.append('\n'.join(prose_lines))
                out.append('')

            i = j + 1
            continue

        out.append(lines[i])
        i += 1

    c = '\n'.join(out)

    # Cleanup broken blocks
    c = re.sub(r'```sql\s*```\s*```', '```\n```', c)
    c = re.sub(r'```\n?```sql', '', c)
    c = re.sub(r'\nsql\n', '\n', c)
    c = re.sub(r'```sql\n\n```', '', c)
    c = c.replace('U+20DE', '')
    c = re.sub(r'\n{4,}', '\n\n\n', c)

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(c)

    sql = c.count('```sql')
    tbls = len(re.findall(r'^\|[ -]+\|', c, re.M))
    imgs = c.count('file:///')
    miss = sum(1 for r in re.findall(r'file:///([^)\s]+)', c) if not os.path.exists(r.rstrip('"')))
    print(f'{note_name}: sql={sql}, tbls={tbls}, imgs={imgs}, miss={miss}')
