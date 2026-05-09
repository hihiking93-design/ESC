#!/usr/bin/env python3
"""
HTML과 generate_all.py의 q1-q4 데이터 순서를 passage 순서에 맞게 재정렬
"""
import re, json
from pathlib import Path

REMAPS = {
    'low1':  [1,2,4,3], 'low4':  [4,1,2,3], 'low10': [1,3,2,4],
    'mid2':  [4,3,1,2], 'mid3':  [4,1,3,2], 'mid4':  [3,1,4,2],
    'mid5':  [3,1,2,4], 'mid6':  [3,1,2,4], 'mid7':  [3,1,2,4],
    'mid8':  [4,1,3,2], 'mid9':  [3,1,2,4], 'mid10': [1,4,2,3],
    'high1': [1,4,2,3], 'high2': [4,1,2,3], 'high3': [4,1,2,3],
    'high4': [4,1,2,3], 'high5': [4,3,1,2], 'high6': [1,2,4,3],
    'high7': [4,2,1,3], 'high8': [4,1,2,3], 'high9': [4,3,1,2],
    'high10':[4,1,2,3],
}

def reorder_set_data(old_data: dict, order: list) -> dict:
    """order[i] = 구 qN → 새 q(i+1) 자리로 재배치"""
    new_data = dict(old_data)  # audio_id, _level, passage 등 보존
    for new_idx, old_n in enumerate(order):
        new_n = new_idx + 1
        fields = ['q', 'A', 'B', 'C', 'D', 'E', 'answer']
        for f in fields:
            old_key = f"{f}{old_n}"
            new_key = f"{f}{new_n}"
            if old_key in old_data:
                new_data[new_key] = old_data[old_key]
    return new_data


# ── HTML 처리 ───────────────────────────────────────────────────────────
REPO = Path(__file__).parent.parent
HTML_PATH = REPO / 'index.html'

def parse_html_sets(html: str) -> list:
    """JS 배열에서 세트 데이터 파싱. 각 { ... } 블록을 dict로 반환."""
    # audio_id 기준으로 각 오브젝트 추출
    sets = []
    # 각 세트 블록 매칭 (다음 { 또는 ] 까지)
    pattern = re.compile(r'\{[^{}]*audio_id:"(\w+)"[^{}]*\}', re.DOTALL)
    for m in pattern.finditer(html):
        block = m.group(0)
        start, end = m.span()
        entry = {'_raw': block, '_span': (start, end)}
        # 모든 key:"value" 추출
        for kv in re.finditer(r'(\w+):"([^"]*)"', block):
            entry[kv.group(1)] = kv.group(2)
        sets.append(entry)
    return sets

def rebuild_block(old_block: str, old_entry: dict, new_entry: dict) -> str:
    """원본 블록 문자열에서 qN/AN/.../answerN 값만 교체"""
    result = old_block
    for n in range(1, 5):
        for f in ['q', 'A', 'B', 'C', 'D', 'E', 'answer']:
            old_key = f"{f}{n}"
            new_val = new_entry.get(old_key, old_entry.get(old_key, ''))
            old_val = old_entry.get(old_key, '')
            if old_val and old_val != new_val:
                # 정확한 key:"value" 치환
                old_str = f'{old_key}:"{old_val}"'
                new_str = f'{old_key}:"{new_val}"'
                result = result.replace(old_str, new_str, 1)
    return result

def fix_html():
    html = HTML_PATH.read_text(encoding='utf-8')
    sets = parse_html_sets(html)

    modified = html
    offset = 0

    for entry in sets:
        aid = entry.get('audio_id', '')
        if aid not in REMAPS:
            continue
        order = REMAPS[aid]
        new_entry = reorder_set_data(entry, order)
        old_block = entry['_raw']
        new_block = rebuild_block(old_block, entry, new_entry)

        if old_block != new_block:
            start, end = entry['_span']
            start += offset
            end += offset
            modified = modified[:start] + new_block + modified[end:]
            offset += len(new_block) - len(old_block)
            print(f'  HTML [{aid}] 수정 완료')

    HTML_PATH.write_text(modified, encoding='utf-8')
    print(f'  → {HTML_PATH} 저장')

# ── generate_all.py 처리 ───────────────────────────────────────────────
GENPY_PATH = REPO / 'scripts' / 'generate_all.py'

def fix_genpy():
    src = GENPY_PATH.read_text(encoding='utf-8')

    # 각 세트 블록 매칭
    pattern = re.compile(r'\{[^{}]*"audio_id":"(\w+)"[^{}]*\}', re.DOTALL)

    result = src
    offset = 0

    for m in pattern.finditer(src):
        block = m.group(0)
        aid = m.group(1)
        if aid not in REMAPS:
            continue
        order = REMAPS[aid]

        # q1-q4 추출
        qs = {}
        for kv in re.finditer(r'"(q[1-4])":"([^"]*)"', block):
            qs[kv.group(1)] = kv.group(2)

        if not qs:
            continue

        # 새 순서로 재배치
        new_qs = {}
        for new_idx, old_n in enumerate(order):
            old_key = f'q{old_n}'
            new_key = f'q{new_idx + 1}'
            if old_key in qs:
                new_qs[new_key] = qs[old_key]

        # 블록 내 치환
        new_block = block
        for n in range(1, 5):
            old_key = f'q{n}'
            old_val = qs.get(old_key, '')
            new_val = new_qs.get(old_key, '')
            if old_val and old_val != new_val:
                new_block = new_block.replace(f'"q{n}":"{old_val}"',
                                              f'"q{n}":"{new_val}"', 1)

        if new_block != block:
            start = m.start() + offset
            end = m.end() + offset
            result = result[:start] + new_block + result[end:]
            offset += len(new_block) - len(block)
            print(f'  generate_all.py [{aid}] 수정 완료')

    GENPY_PATH.write_text(result, encoding='utf-8')
    print(f'  → {GENPY_PATH} 저장')


if __name__ == '__main__':
    print('\n── HTML 수정 ──')
    fix_html()
    print('\n── generate_all.py 수정 ──')
    fix_genpy()
    print('\n완료!')
