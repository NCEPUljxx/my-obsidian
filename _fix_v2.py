import os, re, zipfile
import xml.etree.ElementTree as ET

docx = 'MySQL/MySQL-进阶篇.docx'
img_dir = 'D:/Java/data/MySQL/进阶篇'
os.makedirs(img_dir, exist_ok=True)

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
RN = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

with zipfile.ZipFile(docx) as z:
    # Extract images
    rels_el = ET.fromstring(z.read('word/_rels/document.xml.rels'))
    rid_map = {}
    for rel in rels_el:
        t = rel.get('Target','')
        if 'image' in rel.get('Type','').lower() or 'media' in t:
            fn = os.path.basename(t)
            rid_map[rel.get('Id')] = fn
            zp = 'word/' + t.replace(chr(92), '/')
            if zp in z.namelist():
                with open(os.path.join(img_dir, fn), 'wb') as o:
                    o.write(z.read(zp))

    doc_xml = z.read('word/document.xml')
    root = ET.fromstring(doc_xml)

# Delete decorative
for f in list(os.listdir(img_dir)):
    if os.path.getsize(os.path.join(img_dir,f)) < 500:
        os.remove(os.path.join(img_dir,f))

img_files = set(os.listdir(img_dir))
print(f'Images: {len(img_files)}')

# ====== Parse with TABLE support ======
body = root.find(W + 'body')
out = []
in_code_block = False

for elem in body:
    tag = elem.tag.split('}')[-1]

    if tag == 'p':
        # Images
        imgs = []
        for il in elem.iter(WP + 'inline'):
            for bl in il.iter(A + 'blip'):
                r = bl.get(RN + 'embed')
                if r and r in rid_map:
                    imgs.append(rid_map[r])
        for an in elem.iter(WP + 'anchor'):
            for bl in an.iter(A + 'blip'):
                r = bl.get(RN + 'embed')
                if r and r in rid_map:
                    imgs.append(rid_map[r])

        text = ''
        for re_e in elem.iter(W + 'r'):
            for t in re_e.iter(W + 't'):
                if t.text:
                    text += t.text
        s = text.strip()

        for img in imgs:
            stem = img.rsplit('.',1)[0]
            actual = img
            for af in img_files:
                if af.rsplit('.',1)[0] == stem:
                    actual = af; break
            ref = '![](' + img_dir + '/' + actual + ')'
            if ref not in out: out.append(ref)

        if not s:
            out.append('')
            continue

        # Heading
        if len(s) < 100:
            if re.match(r'^\d+\.\d+\.\d+\.\d+\s', s): out.append('#### ' + s)
            elif re.match(r'^\d+\.\d+\.\d+\s', s): out.append('#### ' + s)
            elif re.match(r'^\d+\.\d+\s', s): out.append('### ' + s)
            elif re.match(r'^\d+\.\s', s): out.append('## ' + s)
            else: out.append(s)
        else:
            out.append(s)

    elif tag == 'tbl':
        # Extract table as markdown
        rows_data = []
        for tr in elem.iter(W + 'tr'):
            cells = []
            for tc in tr.iter(W + 'tc'):
                cell_text = ''
                for t in tc.iter(W + 't'):
                    if t.text: cell_text += t.text
                cells.append(cell_text.strip().replace('\n',' ').replace('\r',' '))
            rows_data.append(cells)

        if len(rows_data) < 3:
            # Single-row tables are likely code boxes
            if rows_data:
                code_text = ' '.join(rows_data[0])
                # Split on line numbers
                parts = re.split(r'\s*\d{1,3}\s{2,}', code_text)
                code = [p.strip() for p in parts if p.strip()]
                if code:
                    out.append('')
                    out.append('```sql')
                    out.extend(code)
                    out.append('```')
                    out.append('')
            continue

        # Multi-row table: convert to markdown
        mc = max(len(r) for r in rows_data)
        for r in rows_data:
            while len(r) < mc: r.append('')

        # Check if table content looks like CODE (starts with SQL keywords)
        all_sql = True
        for r in rows_data:
            for cell in r:
                if cell and not re.match(r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|SHOW|SET|DESC|EXPLAIN|GRANT|REVOKE|TRUNCATE|FLUSH|USE|LOAD|mysql|mysqldump|docker|net)\b', cell, re.I):
                    if cell.strip():
                        all_sql = False; break
            if not all_sql: break

        if all_sql:
            # Code table → extract as ```sql
            code_lines = []
            for r in rows_data:
                for cell in r:
                    if cell.strip():
                        # Split line-numbered code
                        parts = re.split(r'\s*\d{1,3}\s{2,}', cell.strip())
                        for p in parts:
                            p = p.strip()
                            if p and len(p) > 2:
                                code_lines.append(p)

            if code_lines:
                out.append('')
                out.append('```sql')
                out.extend(code_lines)
                out.append('```')
                out.append('')
            continue

        # Normal table
        tbl = '| ' + ' | '.join(rows_data[0]) + ' |\n'
        tbl += '| ' + ' | '.join(['---']*mc) + ' |\n'
        for r in rows_data[1:]:
            tbl += '| ' + ' | '.join(r) + ' |\n'
        out.append('')
        out.append(tbl.rstrip())
        out.append('')

content = '\n'.join(out)

# ====== Post-process: fix line-numbered SQL outside blocks ======
# Pattern: "1   create procedure ...2   begin3   declare..."
# Split into individual lines and wrap in ```sql
def fix_merged_sql(m):
    return ''  # Remove the merged line entirely (it came from table extraction)

# Find lines with repeating "digit+spaces+code" patterns
lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    s = lines[i].strip()

    # Skip empty lines, headings, images, tables
    if not s or s.startswith('#') or s.startswith('![') or s.startswith('|') or s.startswith('```'):
        fixed_lines.append(lines[i])
        i += 1
        continue

    # Detect line-numbered merged code: "1   keyword...2   keyword...3   keyword..."
    # Has at least 2 line-number + code segments
    segments = [(m.start(), m.end(), m.group(1), m.group(2))
                for m in re.finditer(r'(\d{1,3})\s{2,}([A-Za-z])', s)]

    if len(segments) >= 2:
        # Split and extract code
        parts = re.split(r'(\d{1,3}\s{2,})', s)
        code_lines = []
        for part in parts:
            part = part.strip()
            if part and not re.match(r'^\d{1,3}\s{2,}$', part) and not re.match(r'^\d{1,3}$', part):
                code_lines.append(part)

        if len(code_lines) >= 2:
            fixed_lines.append('')
            fixed_lines.append('```sql')
            fixed_lines.extend(code_lines)
            fixed_lines.append('```')
            fixed_lines.append('')
            i += 1
            continue

    fixed_lines.append(lines[i])
    i += 1

content = '\n'.join(fixed_lines)

# ====== Image paths ======
prefix = 'file:///D:/Java/data/MySQL/进阶篇/'
content = content.replace('![](' + img_dir + '/', '![](' + prefix)

def fix_img(m):
    path = m.group(1)
    fn = path.rsplit('/',1)[-1]
    stem = fn.rsplit('.',1)[0]
    for af in img_files:
        if af.rsplit('.',1)[0] == stem:
            return '![](' + prefix + af + ')'
    return ''

content = re.sub(r'!\[\]\((?:file:///)?D:/Java/data/MySQL/进阶篇/([^)]+)\)', fix_img, content)

# ====== Cleanup ======
# Remove excessive blank lines
while '\n\n\n\n' in content:
    content = content.replace('\n\n\n\n', '\n\n\n')
content = re.sub(r'```sql\s*```\n?', '', content)

# Title + footer
content = '# MySQL 进阶篇\n\n' + content
content += '\n\n---\n\n> 📎 **相关笔记**：[[MySQL-基础篇]] · [[MySQL-运维篇]] · [[MySQL 索引]] · [[JavaWeb/02-数据库与持久层|JavaWeb 持久层]]\n'

with open('MySQL/MySQL-进阶篇.md', 'w', encoding='utf-8') as f:
    f.write(content)

# ====== Verify ======
# Remove orphan disk images
refs = set()
for m in re.finditer(r'file:///D:/Java/data/MySQL/进阶篇/([^)]+)', content):
    refs.add(m.group(1))
for f in list(os.listdir(img_dir)):
    if f not in refs:
        os.remove(os.path.join(img_dir, f))

imgs = len(re.findall(r'file:///D:', content))
miss = sum(1 for r in re.findall(r'file:///([^)\\s]+)', content)
           if not os.path.exists(r.rstrip('"')))
disk = len(os.listdir(img_dir))
lines_count = len(content.split('\n'))

print('Lines: ' + str(lines_count))
print('Images: ' + str(imgs) + ' refs, ' + str(miss) + ' missing, ' + str(disk) + ' on disk')

# Check key areas
for tag in ['2.4', '4.2.2', '4.2.6', '4.2.10', '4.2.11', '4.4.2', '4.4.3']:
    idx = content.find(tag)
    if idx >= 0:
        print('\n=== ' + tag + ' ===')
        for line in content[max(0,idx-5):idx+400].split('\n')[:15]:
            print(line.rstrip()[:140])
