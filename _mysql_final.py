"""
FINAL MySQL notes formatter. One pass, handles everything.
"""
import os, re, shutil

NOTES = {
    'MySQL-基础篇.md': '基础篇',
    'MySQL-进阶篇.md': '进阶篇',
    'MySQL-运维篇.md': '运维篇',
}

IMG_BASE = 'D:/Java/data/MySQL'

# ==== STEP 0: Prepare image directories from docx ====
for doc_name in ['MySQL-基础篇.docx', 'MySQL-进阶篇.docx', 'MySQL-运维篇.docx']:
    print(f'Extracting images from {doc_name}...')
    import zipfile
    docx_path = os.path.join('MySQL', doc_name)
    if not os.path.exists(docx_path):
        continue

    img_key = doc_name.replace('.docx', '.md')
    img_name = NOTES.get(img_key, '')
    if not img_name:
        continue

    img_dir = os.path.join(IMG_BASE, img_name)
    os.makedirs(img_dir, exist_ok=True)

    with zipfile.ZipFile(docx_path) as z:
        for f in z.namelist():
            if 'media/' in f and f.endswith(('.png','.jpg','.jpeg','.gif','.bmp')):
                dst = os.path.join(img_dir, os.path.basename(f))
                if not os.path.exists(dst):
                    with open(dst, 'wb') as out:
                        out.write(z.read(f))
    print(f'  {len(os.listdir(img_dir))} images')

# ==== STEP 1: Fix image refs in all notes ====
for note, img_name in NOTES.items():
    fpath = os.path.join('MySQL', note)
    with open(fpath, encoding='utf-8') as f:
        c = f.read()

    img_dir = os.path.join(IMG_BASE, img_name)
    img_files = set(os.listdir(img_dir))

    # Fix ALL image references: match any path format, resolve to correct extension
    def fix_img(m):
        path = m.group(1).replace('\\', '/')
        fn = path.rsplit('/',1)[-1]
        stem = fn.rsplit('.',1)[0] if '.' in fn else fn
        for af in img_files:
            if af.rsplit('.',1)[0] == stem:
                return f'![]({img_dir}/{af})'
        return m.group(0)

    c = re.sub(r'!\[\]\(([^)]+)\)', fix_img, c)
    c = re.sub(r'!\[[^\]]*\]\(([^)]+)\)', fix_img, c)

    # Add file:/// prefix
    prefix = 'file:///' + IMG_BASE + '/'
    c = c.replace(IMG_BASE + '/', prefix)
    c = re.sub(r'!\[\]\((?!(?:file|http))', '![]({file:///', c)
    c = c.replace('{file:///', 'file:///')

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'{note}: {c.count("file:///")} image refs')

# ==== STEP 2: Comprehensive content cleaning ====
SQL_KWS = (
    'SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|SHOW|SET|DESC|EXPLAIN|'
    'GRANT|REVOKE|TRUNCATE|FLUSH|USE|LOAD|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|'
    'VALUES|INTO|GLOBAL|LOCAL|INFILE|ENGINE|PRIMARY|KEY|INDEX|NULL|NOT|'
    'AUTO_INCREMENT|BEGIN|COMMIT|ROLLBACK|CALL|DECLARE|RENAME|UNIQUE|FOREIGN|'
    'REFERENCES|DEFAULT|CHARSET|COLLATE|CHAR|VARCHAR|INT|BIGINT|TINYINT|'
    'DOUBLE|FLOAT|TEXT|DATE|CONSTRAINT|ADD|MODIFY|COLUMN|IF|THEN|ELSE|WHILE|'
    'REPEAT|ORDER|GROUP|HAVING|LIMIT|UNION|RETURNS|CURSOR|FETCH|DECLARE|'
    'MASTER|SLAVE|GRANT|REVOKE|PARTITION|TRIGGER|PROCEDURE|FUNCTION|'
    'VIEW|COUNT|SUM|AVG|MAX|MIN|IN|LIKE|BETWEEN|EXISTS|DISTINCT|'
    'SCHEMA|DATABASES|TABLES|STATUS|VARIABLES|ENGINES'
)
SQL_RE = re.compile(f'^({SQL_KWS})\\b', re.I)

for note, img_name in NOTES.items():
    fpath = os.path.join('MySQL', note)
    with open(fpath, encoding='utf-8') as f:
        raw = f.read()

    raw = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = raw.split('\n')
    out = []
    in_code_block = False
    i = 0

    while i < len(lines):
        s = lines[i].strip()

        # ---- Handle code block fences ----
        if s in ('```sql', '```', '```java', '```bash', '```xml'):
            fence_type = s
            # Don't toggle - just mark entry
            j = i + 1
            block_lines = []
            while j < len(lines) and lines[j].strip() not in ('```', '```sql', '```java', '```bash', '```xml'):
                block_lines.append(lines[j])
                j += 1

            has_close = j < len(lines)

            # Process block content
            code = []
            prose = []
            for bl in block_lines:
                bs = bl.strip()

                if not bs:
                    code.append('')
                    continue

                # Fix: | 1  ... → just the content (strip fake table format)
                bs_stripped = bs
                m = re.match(r'^\|\s*\d{1,3}\s{2,}(.+?)\s*\|?\s*$', bs)
                if m:
                    bs_stripped = m.group(1).strip()

                has_cn = any(ch >= '一' and ch <= '鿿' for ch in bs_stripped)

                # SQL statements
                if SQL_RE.match(bs_stripped):
                    code.append(bs_stripped)
                elif bs_stripped.startswith('--'):
                    code.append(bs_stripped)
                elif has_cn and not SQL_RE.match(bs_stripped):
                    # Chinese text that's not a SQL statement → prose
                    prose.append(bs_stripped)
                elif re.match(r'^[`)\w]', bs_stripped) and len(bs_stripped) > 2:
                    code.append(bs_stripped)
                elif bs_stripped.startswith('#'):
                    # Remove stray # from prose
                    bs_stripped = bs_stripped.lstrip('#').strip()
                    prose.append(bs_stripped)
                elif re.match(r'^\d{1,3}$', bs_stripped):
                    continue  # standalone line numbers
                else:
                    code.append(bs_stripped)

            # Trim empty lines
            while code and code[0].strip() == '':
                code.pop(0)
            while code and code[-1].strip() == '':
                code.pop(-1)

            if code:
                out.append('```sql')
                out.extend(code)
                out.append('```')
                out.append('')

            if prose:
                for pl in prose:
                    out.append(pl)
                out.append('')

            i = j + 1 if has_close else j
            continue

        # ---- Handle fake table rows (| N  ...) outside code blocks ----
        m = re.match(r'^\|\s*\d{1,3}\s{2,}(.+)$', s)
        if m and not in_code_block:
            content = m.group(1).strip()
            # Check if this looks like SQL
            if SQL_RE.match(content) or content.startswith('--'):
                out.append('```sql')
                out.append(content)
                out.append('```')
                out.append('')
                i += 1
                continue
            elif re.match(r'^(mysql|mysqldump|docker|net\s)', content):
                out.append('```bash')
                out.append(content)
                out.append('```')
                out.append('')
                i += 1
                continue
            else:
                out.append(content)
                out.append('')
                i += 1
                continue

        # ---- Handle bare SQL outside code blocks ----
        if (SQL_RE.match(s) or re.match(r'^(mysql|mysqldump|docker|net\s)\s', s)) and not in_code_block and not s.startswith('!'):
            sql_buf = [lines[i]]
            j = i + 1
            while j < len(lines):
                js = lines[j].strip()
                if js in ('```', '```sql') or js.startswith('#') or js.startswith('![]('):
                    break
                if not js:
                    sql_buf.append('')
                    j += 1
                    continue
                if any(ch >= '一' and ch <= '鿿' for ch in js) and not SQL_RE.match(js):
                    break  # Chinese text ends the SQL block
                if SQL_RE.match(js) or js.startswith('--'):
                    # Clean |N prefix
                    cleaned = js
                    m2 = re.match(r'^\|\s*\d{1,3}\s{2,}(.+?)\s*\|?\s*$', js)
                    if m2:
                        cleaned = m2.group(1).strip()
                    sql_buf.append(cleaned)
                    j += 1
                elif re.match(r'^[`)\w]', js):
                    sql_buf.append(js)
                    j += 1
                else:
                    break

            fence = '```sql'
            if any(re.match(r'^(mysql|mysqldump|docker|net\s)', x.strip()) for x in sql_buf):
                fence = '```bash'

            out.append(fence)
            out.extend(sql_buf)
            out.append('```')
            out.append('')
            i = j
            continue

        # ---- Fix stray #text (not markdown headings, leftover Word formatting) ----
        if re.match(r'^#[a-zA-Z一-鿿]', s) and not re.match(r'^#{1,6}\s', s):
            stripped = s.lstrip('#').strip()
            out.append(stripped)
            out.append('')
            i += 1
            continue

        out.append(lines[i])
        i += 1

    c = '\n'.join(out)

    # ---- Post-processing ----
    # Remove empty code blocks
    c = re.sub(r'```sql\s*```\n?', '', c)
    c = re.sub(r'```bash\s*```\n?', '', c)

    # Remove consecutive fences
    c = re.sub(r'```(?:sql|bash)\n+```(?:sql|bash)\n*', '', c)

    # Remove blank lines between table rows
    for _ in range(5):
        c = re.sub(r'(\|.+\|)\n\n(\|.+\|)', r'\1\n\2', c)

    # Remove decorative chars
    c = c.replace(chr(0x20DE), '')  # combining enclosing square

    # Clean whitespace
    c = re.sub(r'\n{4,}', '\n\n\n', c)

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(c)

    # Stats
    sql_blocks = c.count('```sql')
    tables = len(re.findall(r'^\|[ -]+\|', c, re.M))
    imgs = c.count('file:///')
    miss = sum(1 for r in re.findall(r'file:///([^)\\s]+)', c) if not os.path.exists(r.rstrip('"')))
    fake_tables = len(re.findall(r'^\|\s*\d{1,3}\s{2,}', c, re.M))
    bare_sql = 0
    in_block = False
    for line in c.split('\n'):
        sl = line.strip()
        if sl in ('```sql', '```bash', '```'): in_block = not in_block; continue
        if not in_block and SQL_RE.match(sl):
            bare_sql += 1

    print(f'{note}: sql={sql_blocks}, tbls={tables}, imgs={imgs}, miss={miss}, fake-tbl={fake_tables}, bare={bare_sql}')

print('\nDONE!')
