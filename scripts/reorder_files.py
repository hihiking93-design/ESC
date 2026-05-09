#!/usr/bin/env python3
"""
지문 순서 기준으로 q1~q4 오디오 파일 rename
passage_order[i] = 'qX' → 새 q(i+1).mp3 = 구 qX.mp3
"""
from pathlib import Path
import shutil

# 검증 결과 기반 remapping
# passage_order[i] = 구 qX → 새 q(i+1) 자리로
REMAPS = {
    # LOW
    'low1':  ['q1', 'q2', 'q4', 'q3'],
    'low4':  ['q4', 'q1', 'q2', 'q3'],
    'low10': ['q1', 'q3', 'q2', 'q4'],
    # MID
    'mid2':  ['q4', 'q3', 'q1', 'q2'],
    'mid3':  ['q4', 'q1', 'q3', 'q2'],
    'mid4':  ['q3', 'q1', 'q4', 'q2'],
    'mid5':  ['q3', 'q1', 'q2', 'q4'],
    'mid6':  ['q3', 'q1', 'q2', 'q4'],
    'mid7':  ['q3', 'q1', 'q2', 'q4'],
    'mid8':  ['q4', 'q1', 'q3', 'q2'],
    'mid9':  ['q3', 'q1', 'q2', 'q4'],
    'mid10': ['q1', 'q4', 'q2', 'q3'],
    # HIGH
    'high1':  ['q1', 'q4', 'q2', 'q3'],
    'high2':  ['q4', 'q1', 'q2', 'q3'],
    'high3':  ['q4', 'q1', 'q2', 'q3'],
    'high4':  ['q4', 'q1', 'q2', 'q3'],
    'high5':  ['q4', 'q3', 'q1', 'q2'],
    'high6':  ['q1', 'q2', 'q4', 'q3'],
    'high7':  ['q4', 'q2', 'q1', 'q3'],
    'high8':  ['q4', 'q1', 'q2', 'q3'],
    'high9':  ['q4', 'q3', 'q1', 'q2'],
    'high10': ['q4', 'q1', 'q2', 'q3'],
}

LEVEL_MAP = {
    'low':  'low',
    'mid':  'mid',
    'high': 'high',
}

REPO = Path(__file__).parent.parent
DIRS = [
    REPO / 'lt',
    REPO / 'scripts' / 'output',
]


def rename_set(folder: Path, aid: str, order: list):
    """temp 파일 경유로 사이클 없이 안전하게 rename"""
    # 순서가 같은 경우 skip
    if order == ['q1', 'q2', 'q3', 'q4']:
        return

    # 구 파일명 → 신 파일명 매핑
    mapping = {}  # old_name → new_name
    for new_idx, old_q in enumerate(order):
        new_q = f'q{new_idx + 1}'
        if old_q != new_q:
            old_f = folder / f'{aid}_{old_q}.mp3'
            new_f = folder / f'{aid}_{new_q}.mp3'
            mapping[old_f] = new_f

    if not mapping:
        return

    # 존재 확인
    for f in mapping:
        if not f.exists():
            print(f'  ⚠ 파일 없음: {f}')
            return

    # temp 이름으로 먼저 이동
    temp_map = {}
    for old_f, new_f in mapping.items():
        tmp = old_f.with_suffix('.tmp.mp3')
        shutil.move(str(old_f), str(tmp))
        temp_map[tmp] = new_f

    # temp → 최종 이름
    for tmp, new_f in temp_map.items():
        shutil.move(str(tmp), str(new_f))

    changed = [f'{Path(o).stem}→{Path(n).stem}' for o, n in zip(mapping, mapping.values())]
    print(f'  [{aid}] ' + ', '.join(changed))


def main():
    for base_dir in DIRS:
        if not base_dir.exists():
            print(f'디렉토리 없음: {base_dir}')
            continue
        print(f'\n── {base_dir} ──')
        for aid, order in REMAPS.items():
            level = ''.join(c for c in aid if c.isalpha())  # 'low','mid','high'
            folder = base_dir / level
            rename_set(folder, aid, order)

    print('\n완료!')


if __name__ == '__main__':
    main()
