# 듣기 모드 — 설계 명세 (Phase 1 산출물)

> 첫 빌드 종목. 기존 `index.html`(적응형 한국어 청해)을 공유 셸 위의 "듣기 모드"로
> 재구성한다. 자산(오디오150·문항)·알고리즘이 이미 있어 셸 확립용 최저비용 슬라이스.

---

## 1. 치료목표 · 기둥 매핑

| 기둥 | 이 모드에서의 훈련 | 측정 신호 |
|------|------------------|----------|
| ①듣기능력 (주) | 음성 지문을 듣고 세부정보(색·수·순서) 보유·인출 | 정답률, 레벨 도달 |
| ③속도 (부) | 재생속도 0.6→1.5x 적응 + 응답 반응시간(RT) | 최종 속도, 평균 RT |
| ⑤끈기 (정서, 부) | ~80% 무좌절 난이도 → "할 만하다" 경험으로 이탈 방지 | 완주율, 중도이탈 |

→ 듣기 모드는 **①을 메인으로, ③·⑤를 부수적으로** 건드린다. ②집중(듀얼태스크)은 집중 모드 담당.

## 2. 기존 자산·코드 인벤토리 (재사용 대상)

`index.html`(1471줄)에서 그대로 살릴 것:

- **데이터**: `LOW`/`MID`/`HIGH` 각 세트 `{audio_id,_level,passage,q1..q4,A1..E4,answer1..4}` (5지선다, E="모르겠음"). 오디오 상대경로 `lt/{low,mid,high}/{level}{n}_passage.mp3`·`_q1..q4.mp3`. **150 클립.**
- **적응엔진**(812–906): `initPools`(레벨별 셔플 풀) / `pickNextSet`(현 레벨 우선, 소진 시 타 레벨) / `getSetAccuracy` / `adaptLevel` / `shouldStop` / `countQ`.
- **상수**(815·911): `MAX_SETS=5, MIN_SETS=3`, `SPEED_MIN=0.6, SPEED_MAX=1.5`, `currentLevel='중수'` 시작.
- **속도/오디오 재생**: `currentAudio.playbackRate`, 재생 실패 catch→`finish()`(808–809).
- 3화면 상태기계(start/test/result), 결과 엑셀/이미지 저장(xlsx·html-to-image), 숨김 개발자모드(`pdkcap`).

버릴/격리할 것: 죽은 Gemini 키(`scripts/generate_all.py`), `snap_*.md` 잔재(무관).

## 3. 적응 파라미터 — 결정

**기존 임계값 규칙(현행, 검증된 동작)**:
- 100% → 승급 + 속도+0.1 (고수 만점=즉시 종료 `perfectClear`)
- 75%+ → 승급 + 속도+0.1 (고수는 2연속 통과 필요 `consecutiveHighPass`)
- 50–74% → 유지
- <50% → 강등 + 속도−0.1
- 종료: 만점클리어 / `MAX_SETS=5` 도달 / (≥`MIN_SETS=3` & 고수 2연속) / 풀 소진

**결정**: Phase 1~2에서는 **기존 임계값 규칙을 그대로 유지**한다(이미 난이도를 사용자 능력 근처로 수렴시킴, 재작성은 과잉). 단 목표를 "정답률 ~80% 유지 구간"으로 **명시적 재해석**하고, Phase 3에서 `simulate.py`로 가짜 학습자 모델을 돌려 **실제 수렴 정확도**를 측정한다. 80%에서 크게 벗어나면 그때 weighted up-down(step_down/step_up=0.25) staircase로 마이그레이션 결정. → **가정: 기존 규칙이 80% 근처로 수렴한다(Phase 3에서 검증, 미검증 시 교체).**

세트당 문항수 = 4 고정(현행). `shuffleQuestions`(정답률 75%+ 시 문항 순서 셔플)는 유지.

## 4. 공유 셸 인터페이스 계약 (듣기 모드 구현)

```
listeningMode = {
  id: 'listening', title: '듣기 모드', pillars: ['듣기','속도','끈기'],
  start(config, ctx) {
    // config: { startLevel:'중수', startSpeed:1.0 }
    // ctx.log(event)  → 텔레메트리
    // ctx.onComplete(result) → 셸이 보상·진정 인터루드·홈복귀 처리
    // 내부: initPools → (pickNextSet → 재생 → 응답수집 → adaptLevel → shouldStop) 루프
  }
}
```
result 형태: `{ mode:'listening', sets, finalLevel, finalSpeed, overallAccuracy, avgRT, completed:true }`

## 5. 텔레메트리 이벤트 스키마 (가명, 비의료)

| event | 필드 | 발화 시점 |
|-------|------|----------|
| `session_started` | mode, anonId, startLevel, startSpeed, ts | 모드 진입 |
| `set_started` | setNum, level, speed, audioId, ts | 세트 시작 |
| `answer_submitted` | setNum, qIdx, choice, correct, rtMs, ts | 문항 응답 |
| `level_adapted` | fromLevel, toLevel, fromSpeed, toSpeed, setAccuracy, ts | adaptLevel 후 |
| `session_completed` | sets, finalLevel, finalSpeed, overallAccuracy, avgRt, completed, ts | 종료 |

- `anonId` = 기기 로컬 생성 가명(예: localStorage UUID). PII 없음.
- 임상지표(d′ 등)는 사용자 비노출, 내부 파생 전용. **이 스키마가 추후 Firehose→S3 이벤트의 원형.**
- `ts`는 클라이언트 시각. (워크플로/결정 재현성 위해 로깅은 이벤트 순서 보존.)

## 6. UI 플로우 · 화면

```
홈(모드 메뉴 + 오늘의 추천)
  └─[듣기 모드 선택]→ 듣기 인트로(목표·시작버튼)
       └─ 세트 진행(지문 재생 → 4문항 응답, 레벨/속도 플래시)  ←─ 루프(최대5)
            └─ 결과(정답률·도달레벨·속도, 무좌절 프레이밍 카피)
                 └─ 진정 인터루드(3호흡)
                      └─ 홈 복귀(스트릭·뱃지 갱신)
```
- 기존 start/test/result 3화면을 듣기 모드 내부로 흡수. 그 **앞단에 홈**, **뒷단에 진정 인터루드**를 셸이 감싼다.
- 모바일 반응형·탭타겟 유지(기존 dev모드 모바일 탭 보존).

## 7. 성공기준 · 검증항목 (Phase별 verify 게이트)

- [ ] 홈→듣기→결과→인터루드→홈 1세션 완주(데스크톱·모바일).
- [ ] 정답/오답/"모르겠음" 3경로 모두 정상 채점·적응.
- [ ] 오디오 로드 실패 시 앱이 죽지 않고 스킵/재시도.
- [ ] 레벨 풀 소진·최소/최대 세트 엣지에서 정상 종료.
- [ ] 텔레메트리 5개 이벤트가 실제로 발화(console/localStorage 확인).
- [ ] 시뮬레이터: 가짜 학습자 수렴 정확도 측정 → 목표 80% 근처(±) 확인 or 튜닝.
- [ ] 비의료 카피 감사 통과(진단·임상 용어 0).
- [ ] Vercel 본인계정 배포 후 라이브 1세션·오디오 재생 확인.

## 8. 비의료 카피 가드 (이 모드)

- 결과화면: "정답률 N% · 도달 레벨 · 듣기 속도" 같은 **학습 표현만**. "진단/수준 판정/ADHD" 금지.
- 무좌절 프레이밍: "거의 다 맞혔어요", "한 단계 올라갈 수 있어요" 톤(⑤끈기·④두려움 둔감화).
- "모르겠음(E)" 선택을 오답이 아닌 **정직한 패스**로 카피상 존중(시험 두려움↓).

---

### Phase 1 산출물 체크 (이 문서로 완료되는 항목)
①기둥매핑 ②자산·코드 인벤토리 ③적응 파라미터 결정(+미검증 가정 명시) ④셸 계약 ⑤텔레메트리 스키마 ⑥UI 플로우 ⑦성공기준·검증항목 ⑧비의료 카피 가드 — **8/8 정의 완료.**

→ 다음: **Phase 2 코어 구현.** 첫 단계 = Desktop\ESC 리팩터 구조 결정(단일 index.html 확장 vs 셸/모드 파일 분리).
