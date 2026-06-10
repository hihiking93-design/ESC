#!/usr/bin/env python3
"""
ESC Listening Test 적응형 알고리즘 시뮬레이션
다양한 학습자 프로파일로 수십 번 돌려서 실제 패턴 관찰
"""
import random, json
from collections import defaultdict

# ── 알고리즘 상수 (JS와 동일) ──────────────────────────────────────────
MAX_SETS   = 5    # prod(index.html)과 동일
MIN_SETS   = 3
SPEED_MIN  = 0.6
SPEED_MAX  = 1.5

LEVELS = ['초보', '중수', '고수']
SET_COUNTS = {'초보': 10, '중수': 10, '고수': 10}

def shuffle(arr):
    a = arr[:]
    random.shuffle(a)
    return a

def make_pools():
    return {lv: list(range(SET_COUNTS[lv])) for lv in LEVELS}

def pick_next(pools, current_level):
    if pools[current_level]:
        return pools[current_level].pop(0), current_level
    for lv in LEVELS:
        if pools[lv]:
            return pools[lv].pop(0), lv
    return None, None

# ── 학습자 프로파일 → 문항 정답 시뮬레이션 ──────────────────────────────
def answer_question(level, q_position, profile):
    """
    profile 구조:
      base_acc:   {'초보': 0.9, '중수': 0.75, '고수': 0.4}
      decay:      문항 위치(0~3)마다 정확도 감소량 (0이면 균일)
      noise:      세트마다 가해지는 랜덤 노이즈 범위
    """
    acc = profile['base_acc'][level]
    acc -= profile['decay'] * q_position   # q_position: 0~3
    acc += random.uniform(-profile['noise'], profile['noise'])
    acc = max(0.0, min(1.0, acc))
    return random.random() < acc

# ── 단일 시뮬레이션 ───────────────────────────────────────────────────
def simulate_student(profile, seed=None):
    if seed is not None:
        random.seed(seed)

    pools = make_pools()
    for lv in LEVELS:
        pools[lv] = shuffle(pools[lv])

    current_level      = '초보'
    current_speed      = 1.0
    consecutive_high   = 0
    perfect_clear      = False
    shuffle_questions  = False

    result_data  = []   # 문항별
    set_history  = []   # 세트별

    set_idx = 0

    while True:
        set_num, set_level = pick_next(pools, current_level)
        if set_num is None:
            break

        # 4문항 답변
        q_order = shuffle(list(range(4))) if shuffle_questions else list(range(4))
        set_results = []
        for pos_idx, q_pos in enumerate(q_order):
            correct = answer_question(set_level, q_pos, profile)
            set_results.append(correct)
            result_data.append({
                '세트': set_idx + 1,
                '난이도': set_level,
                '문항순서': pos_idx + 1,   # 실제 출제 순서 (1~4)
                '문항위치': q_pos + 1,      # 지문 내 원래 위치 (1~4)
                '셔플': shuffle_questions,
                '결과': 'O' if correct else 'X',
            })

        # 세트 정확도
        correct_n = sum(set_results)
        total_n   = len(set_results)
        acc       = correct_n / total_n

        # adaptLevel
        shuffle_questions = acc >= 0.75
        perfect_clear = False

        if acc == 1.0:
            if set_level == '고수':
                perfect_clear = True
            else:
                if current_level == '초보':  current_level = '중수'
                elif current_level == '중수': current_level = '고수'
            consecutive_high = 0
            current_speed = min(SPEED_MAX, round((current_speed + 0.1) * 10) / 10)
        elif acc >= 0.75:
            if set_level == '고수': consecutive_high += 1
            else: consecutive_high = 0
            if current_level == '초보':  current_level = '중수'
            elif current_level == '중수': current_level = '고수'
            current_speed = min(SPEED_MAX, round((current_speed + 0.1) * 10) / 10)
        elif acc < 0.5:
            consecutive_high = 0
            if current_level == '고수':  current_level = '중수'
            elif current_level == '중수': current_level = '초보'
            current_speed = max(SPEED_MIN, round((current_speed - 0.1) * 10) / 10)
        else:
            consecutive_high = 0

        # 판정 텍스트
        if acc == 1.0:
            verdict = '고수 만점→종료' if set_level == '고수' else f'만점→{current_level} 승급'
        elif acc >= 0.75:
            verdict = f'우수→{current_level} 승급' if consecutive_high == 0 or set_level != '고수' else '우수→유지'
        elif acc >= 0.5:
            verdict = '보통→유지'
        else:
            verdict = f'미흡→{current_level} 하향'

        set_history.append({
            '세트': set_idx + 1,
            '난이도': set_level,
            '정답': f'{correct_n}/{total_n}',
            '정답률': round(acc * 100),
            '판정': verdict,
            '속도': current_speed,
        })

        set_idx += 1

        # shouldStop
        done = set_idx
        if perfect_clear: break
        if done >= MAX_SETS: break
        if done >= MIN_SETS and consecutive_high >= 2: break
        if all(len(p) == 0 for p in pools.values()): break

    return result_data, set_history

# ── 집계 분석 ─────────────────────────────────────────────────────────
def analyze(result_data, set_history):
    if not result_data:
        return {}

    total   = len(result_data)
    correct = sum(1 for r in result_data if r['결과'] == 'O')

    # 레벨별 정답률
    by_level = defaultdict(list)
    for r in result_data:
        by_level[r['난이도']].append(r['결과'] == 'O')
    level_acc = {lv: round(sum(v)/len(v)*100) for lv, v in by_level.items()}

    # 문항 순서별 정답률 (1번째 질문 vs 4번째 질문)
    by_pos = defaultdict(list)
    for r in result_data:
        by_pos[r['문항순서']].append(r['결과'] == 'O')
    pos_acc = {pos: round(sum(v)/len(v)*100) for pos, v in by_pos.items()}

    # 문항 지문위치별 정답률 (지문 앞 vs 뒤)
    by_qpos = defaultdict(list)
    for r in result_data:
        by_qpos[r['문항위치']].append(r['결과'] == 'O')
    qpos_acc = {pos: round(sum(v)/len(v)*100) for pos, v in by_qpos.items()}

    # 셔플 전후 정답률
    shuffle_acc  = [r['결과'] == 'O' for r in result_data if r['셔플']]
    noshuf_acc   = [r['결과'] == 'O' for r in result_data if not r['셔플']]
    shuf_rate    = round(sum(shuffle_acc)/len(shuffle_acc)*100) if shuffle_acc else None
    noshuf_rate  = round(sum(noshuf_acc)/len(noshuf_acc)*100) if noshuf_acc else None

    # 최종 레벨
    final_level = set_history[-1]['난이도'] if set_history else '-'
    final_speed = set_history[-1]['속도'] if set_history else 1.0
    n_sets      = len(set_history)

    # 레벨 전환 횟수
    transitions = 0
    for i in range(1, len(set_history)):
        if set_history[i]['난이도'] != set_history[i-1]['난이도']:
            transitions += 1

    set_rates = [s['정답률'] for s in set_history]
    steady = round(sum(set_rates[-2:]) / len(set_rates[-2:])) if set_rates else None

    def _band(r):
        if r >= 100: return '만점'
        if r >= 75:  return '우수(75-99)'
        if r >= 50:  return '보통(50-74)'
        return '미흡(<50)'
    bands = {}
    for r in set_rates:
        b = _band(r); bands[b] = bands.get(b, 0) + 1

    return {
        '총문항': total,
        '최근2세트정답률': steady,
        '세트밴드': bands,
        '총정답률': round(correct/total*100),
        '세트수': n_sets,
        '최종레벨': final_level,
        '최종속도': final_speed,
        '레벨별정답률': level_acc,
        '문항순서별정답률': pos_acc,
        '문항지문위치별정답률': qpos_acc,
        '셔플정답률': shuf_rate,
        '비셔플정답률': noshuf_rate,
        '레벨전환횟수': transitions,
    }

# ── 프로파일 정의 ─────────────────────────────────────────────────────
PROFILES = {
    '고수_균일':     {'base_acc': {'초보': 0.95, '중수': 0.85, '고수': 0.80}, 'decay': 0.00, 'noise': 0.05},
    '중수_균일':     {'base_acc': {'초보': 0.90, '중수': 0.75, '고수': 0.40}, 'decay': 0.00, 'noise': 0.05},
    '초보_균일':     {'base_acc': {'초보': 0.65, '중수': 0.35, '고수': 0.20}, 'decay': 0.00, 'noise': 0.05},
    '고수_후반약':   {'base_acc': {'초보': 0.95, '중수': 0.85, '고수': 0.80}, 'decay': 0.08, 'noise': 0.05},
    '중수_후반약':   {'base_acc': {'초보': 0.90, '중수': 0.80, '고수': 0.45}, 'decay': 0.10, 'noise': 0.05},
    '초보_후반강':   {'base_acc': {'초보': 0.60, '중수': 0.35, '고수': 0.20}, 'decay':-0.07, 'noise': 0.05},
    '중수_불안정':   {'base_acc': {'초보': 0.85, '중수': 0.70, '고수': 0.40}, 'decay': 0.00, 'noise': 0.20},
    '중수상위_경계': {'base_acc': {'초보': 0.95, '중수': 0.80, '고수': 0.55}, 'decay': 0.05, 'noise': 0.08},
    '고수_직진':     {'base_acc': {'초보': 1.00, '중수': 0.90, '고수': 0.85}, 'decay': 0.00, 'noise': 0.03},
    '롤러코스터':    {'base_acc': {'초보': 0.80, '중수': 0.75, '고수': 0.50}, 'decay': 0.00, 'noise': 0.30},
}

# ── 실행 ──────────────────────────────────────────────────────────────
N_RUNS = 30   # 프로파일당 반복 횟수

print('=' * 70)
print('ESC Listening Test 시뮬레이션 결과')
print('=' * 70)

all_results = {}
GLOBAL_RUNS = []

for name, profile in PROFILES.items():
    runs_analysis = []
    sample_history = None

    for i in range(N_RUNS):
        rd, sh = simulate_student(profile, seed=i)
        a = analyze(rd, sh)
        runs_analysis.append(a)
        if i == 0:
            sample_history = sh

    GLOBAL_RUNS.extend(runs_analysis)

    # N_RUNS 평균
    def avg(key):
        vals = [r[key] for r in runs_analysis if r.get(key) is not None]
        return round(sum(vals)/len(vals)) if vals else None

    def avg_dict(key):
        keys = set()
        for r in runs_analysis:
            keys.update(r.get(key, {}).keys())
        return {k: round(sum(r.get(key,{}).get(k,0) for r in runs_analysis)/N_RUNS) for k in sorted(keys)}

    def most_common(key):
        from collections import Counter
        return Counter(r[key] for r in runs_analysis).most_common(1)[0][0]

    print(f'\n▶ [{name}]')
    print(f'  프로파일: 초보={profile["base_acc"]["초보"]:.0%}  중수={profile["base_acc"]["중수"]:.0%}  고수={profile["base_acc"]["고수"]:.0%}  decay={profile["decay"]}  noise={profile["noise"]}')
    print(f'  평균 세트수: {avg("세트수")}  /  평균 총정답률: {avg("총정답률")}%  /  최종레벨(최빈): {most_common("최종레벨")}  /  평균 최종속도: {avg("최종속도")/10:.1f}x' if avg("최종속도") else '')
    print(f'  레벨별 정답률: {avg_dict("레벨별정답률")}')
    print(f'  ★수렴(최근2세트): {avg("최근2세트정답률")}%   세트밴드(평균건수): {avg_dict("세트밴드")}')
    print(f'  문항순서별(출제순): {avg_dict("문항순서별정답률")}')
    print(f'  문항지문위치별:    {avg_dict("문항지문위치별정답률")}')
    shuf = avg('셔플정답률'); noshuf = avg('비셔플정답률')
    if shuf and noshuf:
        print(f'  셔플 전 정답률: {noshuf}%  /  셔플 후 정답률: {shuf}%  (차이: {shuf-noshuf:+}%)')
    print(f'  평균 레벨전환횟수: {avg("레벨전환횟수")}')
    print(f'  샘플 세트 흐름:')
    for sh in sample_history:
        bar = '●' * int(sh['정답률']/25) + '○' * (4 - int(sh['정답률']/25))
        print(f'    세트{sh["세트"]:2d}  {sh["난이도"]}  {bar}  {sh["정답률"]}%  {sh["판정"]}')

    all_results[name] = {
        'profile': profile,
        'avg': {
            '세트수': avg('세트수'),
            '총정답률': avg('총정답률'),
            '최종레벨': most_common('최종레벨'),
            '레벨별정답률': avg_dict('레벨별정답률'),
            '문항순서별정답률': avg_dict('문항순서별정답률'),
            '문항지문위치별정답률': avg_dict('문항지문위치별정답률'),
            '셔플정답률': shuf,
            '비셔플정답률': noshuf,
            '레벨전환횟수': avg('레벨전환횟수'),
        }
    }

# ── 수렴 가정 검증 (Phase 3) ────────────────────────────────────────────
steadies = [r['최근2세트정답률'] for r in GLOBAL_RUNS if r.get('최근2세트정답률') is not None]
agg_bands = {}
for r in GLOBAL_RUNS:
    for b, c in r.get('세트밴드', {}).items():
        agg_bands[b] = agg_bands.get(b, 0) + c
total_sets  = sum(agg_bands.values())
mean_steady = round(sum(steadies)/len(steadies), 1) if steadies else None

print('\n' + '=' * 70)
print('수렴 가정 검증 (Phase 1 가정: 기존 규칙이 ~80% 정답률로 수렴하는가?)')
print('=' * 70)
print(f'  전체 시뮬 세트수: {total_sets}  (프로파일 {len(PROFILES)} × {N_RUNS}회)')
print(f'  평균 수렴 정확도(최근 2세트): {mean_steady}%')
print(f'  세트 정확도 밴드 분포:')
for b in ['만점', '우수(75-99)', '보통(50-74)', '미흡(<50)']:
    c = agg_bands.get(b, 0)
    pct = round(c/total_sets*100) if total_sets else 0
    print(f'    {b:12s} {c:5d}  ({pct}%)')
comfort = agg_bands.get('우수(75-99)', 0) + agg_bands.get('보통(50-74)', 0)
frust   = agg_bands.get('미흡(<50)', 0)
bored   = agg_bands.get('만점', 0)
print(f'  편안(50-99%): {round(comfort/total_sets*100)}%   |   좌절(<50%): {round(frust/total_sets*100)}%   |   지루(만점): {round(bored/total_sets*100)}%')

# JSON 저장
import os
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simulation_results.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'\n결과 저장 → {out_path}')
