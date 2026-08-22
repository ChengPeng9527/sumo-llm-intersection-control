from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from docx import Document

ROOT = Path(r'D:\Sumo\sumo_train')
SRC = ROOT / 'docs' / 'dissertation' / 'full_draft_submission_v6.docx'
DST = ROOT / 'docs' / 'dissertation' / 'full_draft_submission_v7.docx'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def remove_numpr(paragraph):
    pPr = paragraph._p.pPr
    if pPr is None:
        return
    numPr = pPr.numPr
    if numPr is not None:
        pPr.remove(numPr)


doc = Document(SRC)
for para in doc.paragraphs:
    text = para.text
    if text == 'Traffic-level behaviour' and para.style.name == 'List Number':
        para.style = doc.styles['List Bullet']
        remove_numpr(para)
    elif text == 'Provider-level behaviour' and para.style.name == 'List Number':
        para.style = doc.styles['List Bullet']
        remove_numpr(para)
    elif text == '9. Revised RQ summary':
        para.text = '8. Revised RQ summary'
    elif para.style.name in {'List Bullet', 'List Number'} and text.startswith('- '):
        para.text = text[2:]

doc.save(DST)

# Verify counts across all Word XML parts.
with zipfile.ZipFile(DST) as z:
    texts = []
    for name in z.namelist():
        if not (name.startswith('word/') and name.endswith('.xml')):
            continue
        root = ET.fromstring(z.read(name))
        for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            texts.append(t.text or '')
full = '\n'.join(texts)

bad_chars = ['\u5344', '\ufffe', '\ufffd']
bad_char_count = sum(full.count(ch) for ch in bad_chars)
bad_plus_minus_count = full.count('\u5344')
bad_numbering_count = sum(full.count(s) for s in [
    '27. Traffic-level',
    '28. Provider-level',
    '29. The LLM',
    '30. Rule-based',
    '31. The LLM',
    '32. Provider',
    '9. Revised RQ summary',
])
true_pm_count = full.count('±')
print('BAD_CHAR_COUNT', bad_char_count)
print('BAD_PLUS_MINUS_COUNT', bad_plus_minus_count)
print('BAD_NUMBERING_COUNT', bad_numbering_count)
print('TRUE_PLUS_MINUS_COUNT', true_pm_count)
print('HAS_V7', DST.exists(), DST.stat().st_size)
"cleaned to v7" 
