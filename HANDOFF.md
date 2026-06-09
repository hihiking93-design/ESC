# ESC Listening Test — 인수인계 문서

> 적응형 한국어 듣기 진단 웹앱. 정답률에 따라 난이도(초보·중수·고수)와 재생 속도를
> 실시간으로 자동 조정합니다. 단일 HTML 파일(JS/CSS/데이터 전부 내장) 구조.
>
> **이 repo는 자기완결형입니다.** 코드 + 오디오가 한 곳에 있고 오디오 경로는 상대경로라,
> 어디에 배포하든(Vercel·GitHub Pages·로컬) **코드 수정 없이 그대로 동작합니다.**

---

## 📩 인수인계 안내 (실장님께)

> ESC Listening Test 인수인계입니다.
>
> - **소스/문서**: https://github.com/lanssam/ESC_Listening_Test
> - **라이브**: https://esc-listening-test.vercel.app
>
> repo 안 **HANDOFF.md** (이 문서)를 먼저 읽어주세요.
> 운영 · 수정 · 배포 · **본인 계정으로 이관**까지 전부 정리되어 있습니다.
>
> 현재 라이브는 전임자 개인 GitHub/Vercel에 떠 있습니다.
> **본인 계정으로 이관(아래 2번)을 완료하시면 알려주세요. 그때 전임자 계정을 정리하겠습니다.**
> (이관 전까지는 아무것도 삭제하지 않으니 서비스는 계속 정상 작동합니다.)

---

## 1. 지금 상태 (전임자 퇴사 시점 기준)

- **라이브 서비스**: https://esc-listening-test.vercel.app — 정상 작동, 자기완결형
  - 웹앱(`index.html`) + 오디오(`lt/`)가 모두 같은 Vercel 배포에 포함됨
  - 외부 의존(GitHub Pages 등) 없음
- **소스코드**: GitHub `lanssam/ESC_Listening_Test` (public) — 위 라이브와 동일 내용
- **보안**: 오디오 생성에 쓰던 Gemini API 키는 **이미 전부 폐기됨**.
  `scripts/generate_all.py`에 남은 키 문자열은 죽은 키라 무해하나, 새로 쓰려면 본인 키 필요.

> ⚠️ 현재 라이브가 떠 있는 GitHub/Vercel은 **전임자 개인 계정**입니다.
> 서비스를 계속 운영하려면 **자기 계정으로 이관(2번)** 하세요. 안 하면 계정 정리 시 서비스가 멈춥니다.

---

## 2. 자기 계정으로 이관하기 (가장 중요)

repo가 자기완결형이라 절차가 단순합니다. **코드 한 줄 안 고쳐도 됩니다.**

1. 본인 GitHub 계정에 이 repo를 올림
   - 전임자 repo를 fork 하거나, 압축본을 새 repo로 push
2. 본인 Vercel 계정 생성 → **위 GitHub repo를 Import** → 배포
   - 빌드 설정 불필요(정적 사이트). 그대로 Deploy
3. 끝. 새 도메인(`{프로젝트}.vercel.app`)에서 오디오까지 바로 재생됨
4. 점검: `새도메인/` 접속 → 시험 시작 → 첫 지문 소리 확인 / 결과 화면 캡처·엑셀 저장 확인
5. (선택) `intro.html` 안의 안내용 링크 3곳을 새 도메인으로 교체
6. 이관·점검 완료 후 전임자 repo/배포는 정리해도 됨

> Vercel을 GitHub repo와 연결해두면 이후 `git push`만으로 자동 배포됩니다(권장).

---

## 3. 접속 URL

| 용도 | URL |
|---|---|
| 소개 페이지 | https://esc-listening-test.vercel.app/intro.html |
| 시험 앱 | https://esc-listening-test.vercel.app |

(오디오는 같은 도메인의 `/lt/{low,mid,high}/` 에서 서빙됩니다 — 별도 호스팅 없음)

---

## 4. 수정·배포 방법

```bash
git clone https://github.com/{본인계정}/ESC_Listening_Test.git
cd ESC_Listening_Test
# index.html / intro.html 은 단일 파일 — 에디터로 바로 편집, 더블클릭으로 브라우저 확인
git add . && git commit -m "수정 내용"
git push                 # (Vercel 연결 시 자동 배포)
vercel deploy --prod     # CLI 배포 시 (npm i -g vercel)
```

---

## 5. 새 지문(오디오) 추가

오디오는 Gemini TTS로 생성합니다. **전임자 키는 폐기됐으니 본인 Gemini 키 발급 필요.**

```bash
export GEMINI_API_KEY=본인_키
cd scripts
python3 generate_all.py          # output/low|mid|high 에 mp3 생성
# 생성물을 ../lt/{low,mid,high}/ 로 이동 후 commit & push
```

- 대본 원본: `ESC_Listening_Test_.Script.txt`
- 파일명 규칙: `{레벨}{번호}_passage.mp3`, `{레벨}{번호}_q1~q4.mp3`
  (레벨=low/mid/high, 세트당 지문1 + 문항4 = 5파일)
- ⚠️ `generate_all.py` 상단 `API_KEYS = [...]`는 죽은 키 목록 → 본인 키로 교체하거나
  환경변수(`GEMINI_API_KEY`) 방식으로 바꿔 사용 권장

---

## 6. 알고리즘 요약

- 시작: 초보 레벨, 속도 1.0x / 세트 = 4문항(5지선다, E="모르겠음")
- 세트별 판정:
  - 100% 만점 → 속도 +0.1x (고수 만점이면 즉시 종료)
  - 75%+ → 다음 레벨 승급, 속도 +0.1x
  - 50~74% → 현 레벨 유지
  - 50% 미만 → 한 단계 하향, 속도 -0.1x
- 종료: 최소 3세트 후 — 고수에서 2회 연속 75%+ 또는 만점이면 조기 종료, 아니면 **최대 5세트**
- 속도 범위 0.6x~1.5x (알고리즘 결정, 사용자 조절 불가) / 정확도 75%+ 시 문항 순서 셔플
- 상수(`MAX_SETS`, `MIN_SETS` 등)는 `index.html` 상단에서 조정
- 숨김 개발자모드: 데스크톱 `pdkcap` 타이핑 / 모바일 헤더 탭(레벨→속도→레벨→속도→세트)
  → 16배속 + 정답 하이라이트 (테스트용)

---

## 7. 파일 구조

```
ESC_Listening_Test/
├── index.html        앱 본체 (JS/CSS/데이터 내장)
├── intro.html        소개 페이지
├── HANDOFF.md        ← 이 문서
├── ESC_Listening_Test_.Script.txt   지문 대본 원본
├── lt/               오디오 (배포에 포함, 상대경로로 서빙)
│   ├── low/  (초보 50) · mid/ (중수 50) · high/ (고수 50)
└── scripts/          오디오 생성/시뮬레이션 도구 (로컬 전용, 배포 제외)
```

> `snap_*.md` 파일들은 다른 수학 프로젝트 잔재로 이 시험과 무관합니다(삭제 가능).
