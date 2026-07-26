"""
Rebuild MySQL notes properly from docx:
1. Extract images from docx zip → D:/Java/data/MySQL/{dir}/
2. Parse document.xml to get text + image references with correct filenames
3. Output clean markdown with proper image references
"""
import os, re, shutil, zipfile
import xml.etree.ElementTree as ET

VAULT = r"D:\Java\Obisidian笔记"
MD_DIR = os.path.join(VAULT, "MySQL")
IMG_BASE = r"D:\Java\data\MySQL"

# Namespaces
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}

def rebuild_note(docx_name, note_filename, img_subdir, title):
    """Rebuild a note from docx file."""
    docx_path = os.path.join(MD_DIR, docx_name)
    img_dir = os.path.join(IMG_BASE, img_subdir)
    os.makedirs(img_dir, exist_ok=True)

    # Step 1: Extract images from zip
    img_rid_map = {}  # rId → actual filename
    with zipfile.ZipFile(docx_path) as z:
        # Parse document.xml.rels to get rId → image filename mapping
        rels_path = 'word/_rels/document.xml.rels'
        if rels_path in z.namelist():
            rels_tree = ET.fromstring(z.read(rels_path))
            for rel in rels_tree:
                rid = rel.get('Id')
                target = rel.get('Target', '')
                if 'image' in rel.get('Type', '').lower() or target.endswith(('.png','.jpg','.jpeg','.gif','.bmp')):
                    fname = os.path.basename(target)
                    img_rid_map[rid] = fname
                    # Extract image
                    media_path = os.path.join('word', target.replace('\\', '/'))
                    if media_path in z.namelist():
                        dst = os.path.join(img_dir, fname)
                        if not os.path.exists(dst):
                            with open(dst, 'wb') as f:
                                f.write(z.read(media_path))

    print(f"  Extracted {len(img_rid_map)} images to {img_subdir}/")

    # Step 2: Parse document.xml to get text with image markers
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = z.read('word/document.xml')

    root = ET.fromstring(doc_xml)
    body = root.find('.//w:body', NS)

    lines = []

    for para in body:
        # Check if it's a paragraph or table
        if para.tag == f'{{{NS["w"]}}}p':
            text = extract_paragraph(para, img_rid_map, img_dir)
            lines.append(text)
        elif para.tag == f'{{{NS["w"]}}}tbl':
            tbl_md = extract_table(para)
            lines.append(tbl_md)
            lines.append('')

    content = '\n'.join(lines)

    # Step 3: Convert to proper markdown
    content = fix_heading_levels(content)
    content = clean_whitespace(content)
    content = convert_tables_to_md(content)
    content = format_sql_blocks(content)

    # Set title
    content = f'{title}\n\n' + content

    # Add footer
    footer_map = {
        'MySQL-基础篇': '[[MySQL-进阶篇]] · [[MySQL-运维篇]] · [[MySQL 索引]] · [[JavaWeb/02-数据库与持久层|JavaWeb 持久层]]',
        'MySQL-进阶篇': '[[MySQL-基础篇]] · [[MySQL-运维篇]] · [[MySQL 索引]] · [[JavaWeb/02-数据库与持久层|JavaWeb 持久层]]',
        'MySQL-运维篇': '[[MySQL-基础篇]] · [[MySQL-进阶篇]] · [[MySQL 索引]] · [[JavaWeb/02-数据库与持久层|JavaWeb 持久层]]',
    }
    content += f'\n\n---\n\n> 📎 **相关笔记**：{footer_map.get(img_subdir, "")}\n'

    out_path = os.path.join(MD_DIR, note_filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Verify
    img_count = content.count('file:///')
    missing = 0
    for ref in re.findall(r'file:///([^)\s]+)', content):
        if not os.path.exists(ref.rstrip('"')):
            missing += 1

    print(f"  → {note_filename}: {len(content.split(chr(10)))}L, {img_count} imgs, {missing} missing")


def extract_paragraph(para, img_rid_map, img_dir):
    """Extract text and images from a paragraph element."""
    parts = []

    # Check for images (inline drawings)
    for draw in para.iter(f'{{{NS["wp"]}}}inline'):
        for blip in draw.iter(f'{{{NS["a"]}}}blip'):
            embed = blip.get(f'{{{NS["r"]}}}embed')
            if embed and embed in img_rid_map:
                fname = img_rid_map[embed]
                parts.append(f'![]({img_dir}/{fname})')

    # Also check for anchored drawings
    for anchor in para.iter(f'{{{NS["wp"]}}}anchor'):
        for blip in anchor.iter(f'{{{NS["a"]}}}blip'):
            embed = blip.get(f'{{{NS["r"]}}}embed')
            if embed and embed in img_rid_map:
                fname = img_rid_map[embed]
                parts.append(f'![]({img_dir}/{fname})')

    # Extract text
    text = ''
    for r in para.iter(f'{{{NS["w"]}}}r'):
        for t in r.iter(f'{{{NS["w"]}}}t'):
            if t.text:
                text += t.text

    if text.strip():
        parts.insert(0, text.strip())

    return '\n\n'.join(parts) if parts else ''


def extract_table(tbl):
    """Extract a table as markdown."""
    rows = []
    for tr in tbl.iter(f'{{{NS["w"]}}}tr'):
        cells = []
        for tc in tr.iter(f'{{{NS["w"]}}}tc'):
            cell_text = ''
            for p in tc.iter(f'{{{NS["w"]}}}p'):
                for t in p.iter(f'{{{NS["w"]}}}t'):
                    if t.text:
                        cell_text += t.text
            cells.append(cell_text.strip().replace('\n', ' '))
        rows.append(cells)

    if not rows:
        return ''

    max_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < max_cols:
            r.append('')

    md = '| ' + ' | '.join(rows[0]) + ' |\n'
    md += '| ' + ' | '.join(['---'] * max_cols) + ' |\n'
    for row in rows[1:]:
        md += '| ' + ' | '.join(row) + ' |\n'

    return md


def fix_heading_levels(content):
    """Convert numbered headings to markdown headings."""
    lines = content.split('\n')
    result = []

    for line in lines:
        s = line.strip()
        if not s:
            result.append('')
            continue

        # 1. Chapter: "1. MySQL概述" → "## 1. MySQL概述"
        m = re.match(r'^(\d+)\.?\s+(.+?)$', s)
        if m and len(s) < 80 and not any(kw in s.lower() for kw in ['select ', 'insert ', 'create ']):
            result.append(f'## {s}')
            result.append('')
            continue

        # 2. Section: "1.1 数据库" → "### 1.1 数据库"
        m = re.match(r'^(\d+\.\d+)\s+(.+?)$', s)
        if m and len(s) < 80 and not any(kw in s.lower() for kw in ['select ', 'insert ', 'create ']):
            result.append(f'### {s}')
            result.append('')
            continue

        # 3. Sub-section: "1.1.1 xxx" → "#### 1.1.1 xxx"
        m = re.match(r'^(\d+\.\d+\.\d+)\s+(.+?)$', s)
        if m and len(s) < 80:
            result.append(f'#### {s}')
            result.append('')
            continue

        result.append(line)

    return '\n'.join(result)


def clean_whitespace(content):
    """Clean up whitespace and normalize content."""
    # Remove excessive blank lines
    content = re.sub(r'\n{5,}', '\n\n\n', content)
    # Remove empty lines between image references
    content = re.sub(r'(!\[\]\([^)]+\))\n\n(!\[\]\([^)]+\))', r'\1\n\2', content)
    return content


def convert_tables_to_md(content):
    """Convert space-aligned text tables to markdown tables."""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # Detect table: multiple columns separated by 2+ spaces
        if re.search(r'\S\s{2,}\S', s) and not s.startswith('#') and not s.startswith('```') and not s.startswith('!['):
            table_lines = [s]
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('#') and re.search(r'\S\s{2,}\S', lines[j].strip()):
                table_lines.append(lines[j].strip())
                j += 1

            if len(table_lines) >= 2:
                rows = []
                for tl in table_lines:
                    cells = [c.strip() for c in re.split(r'\s{2,}', tl) if c.strip()]
                    rows.append(cells)

                max_cols = max(len(r) for r in rows)
                for r in rows:
                    while len(r) < max_cols:
                        r.append('')

                result.append('')
                result.append('| ' + ' | '.join(rows[0]) + ' |')
                result.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
                for row in rows[1:]:
                    result.append('| ' + ' | '.join(row) + ' |')
                result.append('')

                i = j
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def format_sql_blocks(content):
    """Wrap SQL statements in ```sql blocks."""
    lines = content.split('\n')
    result = []
    in_sql = False
    sql_continuation = False

    sql_pattern = re.compile(
        r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|'
        r'SHOW|DESC|EXPLAIN|GRANT|REVOKE|TRUNCATE|FLUSH)\s',
        re.I
    )
    solo_pattern = re.compile(r'^\s*(VALUES\s*\(|USE\s+\w|FROM\s+\w)', re.I)

    for line in lines:
        s = line.strip()

        # Don't process headings, images, or empty lines as SQL
        if not s or s.startswith('#') or s.startswith('![') or s.startswith('|') or s.startswith('```'):
            if in_sql:
                result.append('```\n')
                in_sql = False
            result.append(line)
            continue

        if sql_pattern.match(s) or solo_pattern.match(s):
            if not in_sql:
                result.append('\n```sql')
                in_sql = True
            result.append(line)
            sql_continuation = True
        elif in_sql:
            # Check if this is still SQL content
            if sql_continuation and len(s) > 5 and not s.startswith('-'):
                result.append(line)
            else:
                result.append('```\n')
                in_sql = False
                sql_continuation = False
                result.append(line)
            sql_continuation = False
        else:
            result.append(line)

    if in_sql:
        result.append('```\n')

    return '\n'.join(result)


# ============================================================
# Execute
# ============================================================

# 1. Clear old MySQL notes (keep docx)
old_notes = [f for f in os.listdir(MD_DIR) if f.endswith('.md')]
for f in old_notes:
    os.remove(os.path.join(MD_DIR, f))
    print(f"  Removed old: {f}")

# 2. Clear old images
for d in os.listdir(IMG_BASE):
    dp = os.path.join(IMG_BASE, d)
    if os.path.isdir(dp):
        shutil.rmtree(dp)
        print(f"  Cleared images: {d}/")

# 3. Rebuild each note
print("\n=== 重建笔记 ===\n")
rebuild_note('MySQL-基础篇.docx', 'MySQL-基础篇.md', '基础篇', '# MySQL 基础篇')
rebuild_note('MySQL-进阶篇.docx', 'MySQL-进阶篇.md', '进阶篇', '# MySQL 进阶篇')
rebuild_note('MySQL-运维篇.docx', 'MySQL-运维篇.md', '运维篇', '# MySQL 运维篇')

# 4. Create index
index = """# MySQL 知识体系

> MySQL 数据库完整学习笔记，三篇覆盖从入门到运维。

| 笔记 | 内容概要 |
|------|----------|
| [[MySQL-基础篇]] | MySQL 概述 → SQL（DDL/DML/DQL/DCL）→ 函数 → 约束 → 多表查询 → 事务 |
| [[MySQL-进阶篇]] | 存储引擎 → 索引 → SQL 优化 → 视图/存储过程/触发器 → 锁 → InnoDB → 管理 |
| [[MySQL-运维篇]] | 日志 → 主从复制 → 分库分表（MyCat）→ 读写分离 |

---

> 📎 [[JavaWeb/02-数据库与持久层|JavaWeb 持久层]] · [[JavaSE 索引|JavaSE]]
"""

with open(os.path.join(MD_DIR, "MySQL 索引.md"), 'w', encoding='utf-8') as f:
    f.write(index)

# 5. Verify ALL references
print("\n=== 验证 ===")
total = 0
missing = 0
for fn in sorted(os.listdir(MD_DIR)):
    if not fn.endswith('.md'):
        continue
    with open(os.path.join(MD_DIR, fn), encoding='utf-8') as f:
        c = f.read()
    refs = re.findall(r'!\[\]\(([^)]+)\)', c)
    total += len(refs)
    for r in refs:
        path = r.replace('\\', '/')
        if not os.path.exists(path):
            missing += 1
            if missing <= 5:
                print(f'  MISSING: {fn} → {os.path.basename(path)}')
    imgs = len(refs)
    h2 = len(re.findall(r'^## ', c, re.M))
    lines = len(c.split('\n'))
    print(f'  {fn}: {lines}L, H2={h2}, imgs={imgs}')

print(f'\nTotal: {total} refs, {missing} missing')
total_imgs = sum(len(files) for _, _, files in os.walk(IMG_BASE))
print(f'Images on disk: {total_imgs}')
print('ALL RESOLVED!' if missing == 0 else 'NEEDS FIX')

# 6. Delete docx from vault (keep only in 资料/ if needed)
# Don't delete - user may want to keep them
print(f'\nDocx files left in MySQL/ for reference:')
for f in sorted(os.listdir(MD_DIR)):
    if f.endswith('.docx'):
        print(f'  {f}')
