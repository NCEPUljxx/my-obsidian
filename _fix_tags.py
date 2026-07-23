import os, re

target_dirs = ['Redis', 'JavaWeb', 'SSM框架', 'MySQL']
fixed = 0

for mod in target_dirs:
    for fname in sorted(os.listdir(mod)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(mod, fname)
        with open(fpath, encoding='utf-8') as f:
            c = f.read()
        orig = c

        # Only fix # in non-code-block, non-heading contexts
        # Strategy: replace bare #hex colors with backtick-wrapped versions
        # Pattern: # followed by 3 or 6 hex chars, NOT at start of line (those are headings)
        c = re.sub(
            r'(?<!^\s*)(?<!\n)(?<!\w)#([0-9a-fA-F]{3})(?![0-9a-fA-F])(?!\s*[{;])',
            r'`#\1`',
            c
        )
        c = re.sub(
            r'(?<!^\s*)(?<!\n)(?<!\w)#([0-9a-fA-F]{6})(?![0-9a-fA-F])(?!\s*[{;])',
            r'`#\1`',
            c
        )

        if c != orig:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(c)
            fixed += 1
            diff = len(re.findall(r'#[0-9a-fA-F]{3,6}', orig)) - len(re.findall(r'#[0-9a-fA-F]{3,6}', c))
            print(f'  Fixed: {mod}/{fname} ({diff} color codes)')

print(f'\nFixed {fixed} files')
