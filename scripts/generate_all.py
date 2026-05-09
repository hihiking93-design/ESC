#!/usr/bin/env python3
"""
ESC Listening Test 전체 오디오 자동 생성 (Gemini TTS, 5키 로테이션)
1세트 = 1회 TTS 호출 → 무음 감지 → 5파일 분리
150개 MP3 파일 → output/low, mid, high
"""

import base64, os, subprocess, sys, time, wave, io, re
from itertools import cycle
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("pip3 install google-genai")
    sys.exit(1)

API_KEYS = [
    "AIzaSyAlfSxjhUY9E6QnY2w03pYIHU2Nac76484",
    "AIzaSyCB1Eo8DVKQ9K7SFuvk3pN9mLzVap_i87o",
    "AIzaSyCDKAwrRFOH1xiSOeiQHnvL6fpy0IFpFes",
    "AIzaSyAz4EZsk1XIOEtuqmAj7DVl0hiOvwarUhs",
    "AIzaSyCkNpn58hvlqbZP9UR6iFuqQuEC75kMKD0",
    "AIzaSyDYSoMN0V5UB9l812nNBEqEDFV12xP7kaQ",
]
key_cycle = cycle(API_KEYS)

MODEL       = "gemini-2.5-flash-preview-tts"
LANG        = "ko-KR"
VOICE       = "Kore"
OUT         = Path(__file__).parent / "output"
SAMPLE_RATE = 24000
SILENCE_PAD = b'\x00' * int(SAMPLE_RATE * 0.8 * 2)

# ── 데이터 (숫자 → 한국어) ─────────────────────────────────────
LOW = [
  { "audio_id":"low1",
    "passage":"빨간 옷을 입은 목수가 다섯 개의 못과 두 개의 망치를 들고 보라색 울타리를 고치고 있습니다. 초록색 긴 생머리에 연두색 원피스를 입은 목수의 아내가 옥수수 여덟 개와 감자 일곱 개를 쪄서 새참으로 나누어 먹습니다.",
    "q1":"목수가 입은 옷의 색은?", "q2":"목수가 고치는 울타리의 색은?",
    "q3":"목수의 아내 원피스 색은?", "q4":"목수의 아내가 찐 옥수수의 수는?" },
  { "audio_id":"low2",
    "passage":"파란 카디건을 입은 사서가 목요일 오후 세 시에 책 스물세 권을 새 서가에 정리하고 있습니다. 안경을 쓴 남학생 두 명과 머리를 묶은 여학생 한 명이 창가 자리에서 함께 수학 공부를 하고 있으며, 책상 위에는 빨간 형광펜 네 개와 초록 공책 두 권이 놓여 있습니다.",
    "q1":"사서가 입은 옷은?", "q2":"사서가 정리한 책의 수는?",
    "q3":"창가에서 공부하는 학생 수는?", "q4":"책상 위 형광펜 색과 수는?" },
  { "audio_id":"low3",
    "passage":"흰 앞치마를 두른 과일 장수 할머니가 노란 파라솔 아래에서 복숭아 열다섯 개, 자두 스무 개, 포도 세 송이를 팔고 있습니다. 오전 열 시부터 장사를 시작한 할머니는 빨간 운동화를 신고 있으며, 옆에는 손녀로 보이는 단발머리 아이가 분홍 우산을 들고 서 있습니다.",
    "q1":"파라솔의 색은?", "q2":"복숭아는 몇 개?",
    "q3":"할머니가 신은 신발은?", "q4":"아이가 들고 있는 우산 색은?" },
  { "audio_id":"low4",
    "passage":"소풍날 아침 초등학교 삼 학년 교실에서 선생님이 출석을 부르고 있습니다. 파란 모자를 쓴 남학생과 노란 리본을 맨 여학생을 포함해 오늘 결석 없이 스물여덟 명 전원이 등교했습니다. 선생님은 초록색 가방에 김밥 네 줄, 사과 여섯 개, 주스 스물여덟 개를 챙겨 두었습니다.",
    "q1":"파란 모자를 쓴 학생은?", "q2":"오늘 등교한 학생 수는?",
    "q3":"선생님 가방 색은?", "q4":"챙긴 김밥 수는?" },
  { "audio_id":"low5",
    "passage":"일요일 오후 주황색 티셔츠를 입은 아버지가 아들과 함께 동물원에 갔습니다. 기린 두 마리, 코끼리 네 마리, 홍학 아홉 마리가 있는 구역을 지나 펭귄관에 도착했습니다. 펭귄관 앞 매점에서 아이스크림 세 개와 음료수 두 잔을 사서 하늘색 벤치에 앉아 먹었습니다.",
    "q1":"아버지 티셔츠 색은?", "q2":"홍학은 몇 마리?",
    "q3":"매점에서 산 아이스크림 수는?", "q4":"앉아서 먹은 벤치 색은?" },
  { "audio_id":"low6",
    "passage":"화요일 저녁 요리 교실에서 체크무늬 앞치마를 두른 강사가 파스타를 만드는 법을 가르치고 있습니다. 재료로는 토마토 일곱 개, 양파 세 개, 마늘 열두 쪽, 올리브오일이 필요합니다. 수강생 아홉 명 중 다섯 명은 여성이고 네 명은 남성이며, 모두 빨간 앞치마를 두르고 있습니다.",
    "q1":"강사의 앞치마 무늬는?", "q2":"필요한 토마토 수는?",
    "q3":"수강생 중 남성 수는?", "q4":"수강생의 앞치마 색은?" },
  { "audio_id":"low7",
    "passage":"이른 아침 해변에서 하얀 모자를 쓴 노인이 낚싯대 두 개를 드리우고 앉아 있습니다. 파도 소리와 함께 갈매기 일곱 마리가 하늘을 날고, 멀리 빨간 등대가 보입니다. 노인의 양동이에는 이미 고등어 네 마리와 전갱이 여섯 마리가 담겨 있었습니다.",
    "q1":"노인이 쓴 모자 색은?", "q2":"낚싯대는 몇 개?",
    "q3":"하늘을 나는 갈매기 수는?", "q4":"등대의 색은?" },
  { "audio_id":"low8",
    "passage":"병원 대기실에서 파란 점퍼를 입은 할아버지와 분홍 원피스를 입은 손녀가 나란히 앉아 있습니다. 대기번호는 사십칠 번이고 현재 불린 번호는 삼십오 번입니다. 손녀는 노란 가방에서 크레파스 열두 색을 꺼내 도화지에 나무를 그리고 있으며, 그린 나무에는 빨간 사과 다섯 개가 달려 있습니다.",
    "q1":"할아버지 점퍼 색은?", "q2":"손녀의 대기번호는?",
    "q3":"손녀가 꺼낸 크레파스는 몇 색?", "q4":"그림 속 사과 수는?" },
  { "audio_id":"low9",
    "passage":"토요일 오후 실내 체육관에서 파란 유니폼의 팀과 노란 유니폼의 팀이 농구 경기를 벌이고 있습니다. 삼 쿼터 종료 시 파란 팀이 오십육 점, 노란 팀이 사십구 점입니다. 관중석에는 빨간 응원봉을 든 사람들 서른네 명과 초록 풍선을 든 사람들 스물한 명이 앉아 있습니다.",
    "q1":"삼 쿼터 종료 후 파란 팀 점수는?", "q2":"빨간 응원봉 관중 수는?",
    "q3":"현재 리드하는 팀은?", "q4":"초록 풍선 관중 수는?" },
  { "audio_id":"low10",
    "passage":"꽃가게 주인 아주머니가 이른 아침 여섯 시에 가게 문을 열고 장미 서른 송이, 튤립 스물다섯 송이, 해바라기 열 송이를 큰 물통 세 개에 나누어 꽂았습니다. 보라색 앞치마를 두른 아주머니는 하얀 선글라스를 쓰고 있었으며, 오늘 배달 주문이 일곱 건 들어와 있었습니다.",
    "q1":"가게를 연 시각은?", "q2":"물통의 수는?",
    "q3":"아주머니 앞치마 색은?", "q4":"오늘 배달 주문 건수는?" },
]

MID = [
  { "audio_id":"mid1",
    "passage":"지난 토요일 저녁, 한강 공원 야외 무대에서 특별 공연이 열렸습니다. 공연은 오후 일곱 시에 시작되었고, 총 세 팀의 아티스트가 무대에 올랐습니다. 입장은 무료였으며, 현장에는 약 이천 명의 관람객이 모였습니다.",
    "q1":"공연이 열린 장소는 어디입니까?", "q2":"공연에 대한 설명으로 옳지 않은 것은?",
    "q3":"공연에 오른 아티스트 팀 수는?", "q4":"공연 관람객 수는 약 몇 명이었습니까?" },
  { "audio_id":"mid2",
    "passage":"우리 회사는 이번 달부터 주 두 번 재택근무 제도를 도입했습니다. 직원들은 월요일과 금요일 중 하루를 선택해 재택근무를 할 수 있습니다. 단, 월말 보고 기간에는 재택근무가 제한될 수 있습니다.",
    "q1":"재택근무 제도는 언제부터 시작됩니까?", "q2":"이 회사의 재택근무 횟수는 주 몇 회입니까?",
    "q3":"재택근무를 할 수 있는 요일 조합은?", "q4":"재택근무가 제한될 수 있는 경우는?" },
  { "audio_id":"mid3",
    "passage":"박 교수는 오늘 강연에서 디지털 리터러시의 중요성을 강조했습니다. 그는 온라인 정보의 신뢰도 판단, 개인정보 보호, AI 도구의 비판적 활용이 핵심 능력이라고 말했습니다. 또한 이 교육은 학교와 가정 모두에서 이루어져야 한다고 덧붙였습니다.",
    "q1":"오늘 강연의 주제는 무엇입니까?", "q2":"디지털 리터러시에 포함되지 않는 것은?",
    "q3":"박 교수가 핵심 능력으로 언급한 것이 아닌 것은?", "q4":"디지털 리터러시 교육 장소로 언급된 곳은?" },
  { "audio_id":"mid4",
    "passage":"오늘 환경 보호 캠페인에 수백 명의 시민이 참여했습니다. 참가자들은 재활용 가능 소재로 만들어진 피켓을 들고 시내를 행진했습니다. 행사가 끝난 뒤에는 근처 하천에서 쓰레기 줍기 활동도 이어졌습니다.",
    "q1":"캠페인 참가자 수는 어느 정도입니까?", "q2":"피켓의 특징은?",
    "q3":"행진은 어디에서 이루어졌습니까?", "q4":"행사 이후에 진행된 활동은?" },
  { "audio_id":"mid5",
    "passage":"시청 앞 광장에서 오늘 오전 열 시부터 지역 농산물 직거래 장터가 열렸습니다. 참여 농가는 총 서른다섯 곳이며, 판매 품목은 채소류, 과일, 잡곡 등 다양합니다. 행사는 매월 첫째 주 토요일에 정기적으로 개최되며, 오후 네 시에 마감됩니다.",
    "q1":"장터가 시작된 시각은?", "q2":"직거래 장터에 참여한 농가 수는?",
    "q3":"이 행사는 언제 열립니까?", "q4":"장터의 마감 시각은?" },
  { "audio_id":"mid6",
    "passage":"시립 도서관은 이번 달부터 야간 개방 시간을 기존 오후 여섯 시에서 오후 아홉 시로 연장합니다. 또한 어린이 열람실을 새롭게 리모델링하여 좌석 수를 사십 석에서 육십 석으로 늘렸습니다. 단, 노트북 사용은 지정된 구역에서만 가능합니다.",
    "q1":"기존 야간 개방 마감 시각은?", "q2":"도서관 야간 개방 시간이 연장된 시각은?",
    "q3":"어린이 열람실 리모델링 후 좌석 수는?", "q4":"노트북 사용에 관한 설명으로 옳은 것은?" },
  { "audio_id":"mid7",
    "passage":"우리 동네 헬스장이 이달 초 새롭게 문을 열었습니다. 운영 시간은 평일 오전 여섯 시부터 오후 열한 시까지이며, 주말은 오전 여덟 시부터 오후 여덟 시까지입니다. 회원권은 한 달, 세 달, 열두 달 세 가지 종류가 있으며, 등록 첫 달은 가입비가 면제됩니다.",
    "q1":"평일 오픈 시각은?", "q2":"헬스장 주말 마감 시간은?",
    "q3":"회원권 종류에 해당하지 않는 것은?", "q4":"등록 첫 달 혜택은 무엇입니까?" },
  { "audio_id":"mid8",
    "passage":"학교 급식실이 이번 학기부터 잔반 줄이기 캠페인을 시작했습니다. 잔반을 남기지 않은 학생에게는 매주 금요일 특별 후식이 제공됩니다. 지난주 참여율은 전체 학생의 칠십삼 퍼센트였으며, 학교는 이 수치를 구십 퍼센트까지 끌어올리는 것을 목표로 하고 있습니다.",
    "q1":"이 캠페인은 언제 시작했습니까?", "q2":"특별 후식이 제공되는 요일은?",
    "q3":"지난주 캠페인 참여율은?", "q4":"학교가 목표로 하는 캠페인 참여율은?" },
  { "audio_id":"mid9",
    "passage":"이번 주말 지역 문화 센터에서 사진 전시회가 열립니다. 전시 작품은 아마추어 사진작가 열두 명의 작품 총 사십팔 점이며, 자연, 도시, 인물의 세 가지 주제로 구성됩니다. 관람은 무료이며, 전시 기간은 토요일부터 일요일까지 이틀간입니다.",
    "q1":"참여 작가 수는 몇 명입니까?", "q2":"전시 작품의 총 수는?",
    "q3":"전시 주제에 포함되지 않는 것은?", "q4":"전시 관람료는 얼마입니까?" },
  { "audio_id":"mid10",
    "passage":"구청에서는 다음 달부터 무료 외국어 강좌를 운영합니다. 개설 과목은 영어, 일본어, 중국어, 스페인어 네 가지이며, 각 강좌는 주 두 번, 열 주 과정으로 진행됩니다. 신청은 구청 홈페이지 또는 방문 접수로 가능하며, 선착순 스무 명으로 제한됩니다.",
    "q1":"강좌가 개설된 외국어 수는?", "q2":"강좌 개설 언어에 포함되지 않는 것은?",
    "q3":"각 강좌의 진행 기간은?", "q4":"강좌 신청 방법으로 옳지 않은 것은?" },
]

HIGH = [
  { "audio_id":"high1",
    "passage":"최근 연구에 따르면, 도심 내 녹지 면적이 십 퍼센트 증가할 때 도시 평균 기온이 영점오 도 하락하는 것으로 나타났습니다. 이번 연구는 서울, 도쿄, 베를린 등 여러 도시를 대상으로 진행됐습니다. 연구팀은 도심 녹지 확충의 가장 큰 과제로 높은 비용과 토지 확보 문제를 꼽았습니다.",
    "q1":"녹지 십 퍼센트 증가 시 기온 변화는?", "q2":"이 연구에서 측정한 기온 변화의 기준 지표는?",
    "q3":"연구 대상 도시로 언급되지 않은 곳은?", "q4":"도심 녹지 확충의 과제로 언급된 것은?" },
  { "audio_id":"high2",
    "passage":"한 스타트업이 개발한 다국어 번역 앱이 출시 두 달 만에 백만 다운로드를 달성했습니다. 현재 이 앱은 서른두 개 언어를 지원하고 있습니다. 창업자는 향후 의료 및 법률 분야 전문 번역과 기업용 구독 서비스를 추가할 계획이라고 밝혔습니다.",
    "q1":"이 앱을 개발한 주체는?", "q2":"백만 다운로드 달성까지 걸린 시간은?",
    "q3":"현재 지원하는 언어 수는?", "q4":"추가 계획으로 언급되지 않은 것은?" },
  { "audio_id":"high3",
    "passage":"조선 후기 실학자 정약용은 목민심서, 경세유표, 흠흠신서 등 방대한 저술을 남겼습니다. 그의 사상에는 토지 제도 개혁, 관리의 청렴, 서양 기술 수용 등이 담겨 있습니다. 특히 그는 긴 유배 생활 중에도 저술 활동을 멈추지 않았습니다.",
    "q1":"정약용은 어느 시대 인물입니까?", "q2":"정약용 저술로 언급되지 않은 책은?",
    "q3":"정약용 사상에서 강조되지 않은 것은?", "q4":"저술 활동을 이어 간 상황은?" },
  { "audio_id":"high4",
    "passage":"유엔 보고서에 따르면, 전 세계 플라스틱 생산량의 약 사십 퍼센트가 일회용 포장재에 해당합니다. 현재 플라스틱 재활용 비율은 약 구 퍼센트에 불과합니다. 보고서는 생산자 책임 재활용 제도 강화, 바이오 플라스틱 전환, 소비자 교육 프로그램 확대 등을 해결책으로 제안했습니다.",
    "q1":"이 보고서를 발표한 기관은?", "q2":"일회용 포장재 비율은?",
    "q3":"현재 플라스틱 재활용 비율은?", "q4":"제안된 해결책에 포함되지 않는 것은?" },
  { "audio_id":"high5",
    "passage":"국내 한 연구팀이 수면 부족이 인지 기능에 미치는 영향을 분석한 결과를 발표했습니다. 하루 여섯 시간 미만으로 잔 성인 그룹은 일곱에서 여덟 시간 수면 그룹보다 기억력 테스트 점수가 평균 이십이 퍼센트 낮았습니다. 연구팀은 수면 부족이 사흘 이상 지속될 경우 집중력뿐 아니라 감정 조절 능력도 저하된다고 밝혔습니다.",
    "q1":"이 연구의 연구 대상은?", "q2":"연구에서 정상 수면 시간으로 본 범위는?",
    "q3":"수면 여섯 시간 미만 그룹의 기억력 점수 차이는?", "q4":"수면 부족 사흘 이상 지속 시 언급되지 않은 현상은?" },
  { "audio_id":"high6",
    "passage":"올해 서울시가 발표한 교통 혼잡 개선 방안에 따르면, 출퇴근 시간대 버스 전용 차로를 현재보다 십오 킬로미터 연장할 계획입니다. 또한 교차로 신호 체계를 인공지능으로 전환해 평균 대기 시간을 삼십 퍼센트 줄이는 것을 목표로 하고 있습니다. 이 사업은 내년 상반기 착공 예정이며, 완공까지 약 이 년이 소요될 전망입니다.",
    "q1":"버스 전용 차로 연장 계획 거리는?", "q2":"인공지능 신호 체계 도입의 목표는?",
    "q3":"착공 예정 시기는?", "q4":"이 사업의 완공까지 예상 기간은?" },
  { "audio_id":"high7",
    "passage":"조선 시대 화가 김홍도는 서민의 일상을 생동감 있게 담은 풍속화로 유명합니다. 그는 도화서 화원으로 출발해 정조의 두터운 신임을 받았으며, 씨름, 서당, 무동 등의 작품을 남겼습니다. 말년에는 경제적 어려움 속에서도 창작 활동을 이어갔으나, 정확한 사망 연도는 알려져 있지 않습니다.",
    "q1":"김홍도의 그림 장르는?", "q2":"김홍도가 처음 몸담은 직책은?",
    "q3":"김홍도의 작품으로 언급되지 않은 것은?", "q4":"김홍도에 대한 설명으로 옳지 않은 것은?" },
  { "audio_id":"high8",
    "passage":"최근 식품 업계에서는 대체 단백질 식품 시장이 빠르게 성장하고 있습니다. 식물성 단백질과 배양육을 중심으로 한 이 시장은 이천이십삼 년 기준 전 세계 시장 규모가 약 천팔백억 달러에 달하며, 이천삼십 년까지 연평균 구 퍼센트 성장이 예상됩니다. 국내에서도 대형 식품 기업들이 잇따라 대체육 제품을 출시하고 있으나, 가격 경쟁력 확보가 여전히 과제로 남아 있습니다.",
    "q1":"대체 단백질 시장의 중심이 되는 것은?", "q2":"이천이십삼 년 기준 대체 단백질 시장 규모는?",
    "q3":"이천삼십 년까지 예상되는 연평균 성장률은?", "q4":"국내 대체육 시장의 과제로 언급된 것은?" },
  { "audio_id":"high9",
    "passage":"세계보건기구는 최근 보고서에서 도시 지역 소음 공해가 심혈관 질환 발생률을 높인다고 경고했습니다. 보고서에 따르면, 야간 평균 소음이 오십오 데시벨을 초과할 경우 심장병 위험이 유의미하게 증가합니다. WHO는 각국 정부에 방음벽 설치, 교통량 제한, 저소음 도로 포장 등의 조치를 권고했습니다.",
    "q1":"이 보고서를 발표한 기관은?", "q2":"이 보고서가 주목한 소음 공해의 주요 영향은?",
    "q3":"심장병 위험이 높아지는 야간 소음 기준은?", "q4":"WHO가 권고한 조치에 포함되지 않는 것은?" },
  { "audio_id":"high10",
    "passage":"국내 한 대학 연구팀이 청소년의 스마트폰 사용 패턴과 학업 성취도 간의 관계를 분석했습니다. 하루 네 시간 이상 스마트폰을 사용하는 학생 그룹은 두 시간 미만 그룹에 비해 평균 성적이 낮았으나, 스마트폰을 학습 도구로 활용하는 경우에는 성적 차이가 줄어드는 것으로 나타났습니다. 연구팀은 사용 시간 제한보다 사용 목적 교육이 더 효과적이라고 제안했습니다.",
    "q1":"이 연구를 수행한 주체는?", "q2":"성적 차이가 나타난 스마트폰 사용 시간 기준은?",
    "q3":"성적 차이가 줄어든 경우는?", "q4":"연구팀이 제안한 해결책은?" },
]


def pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm + SILENCE_PAD)
    return buf.getvalue()


def generate_combined(texts: list, voice: str) -> bytes:
    combined = "  ".join(texts)
    prompt = f"다음 텍스트를 그대로 읽어주세요: {combined}"
    while True:
        key = next(key_cycle)
        client = genai.Client(api_key=key)
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        ),
                        language_code=LANG,
                    ),
                ),
            )
            if not resp.candidates or not resp.candidates[0].content:
                print("  빈 응답, 재시도...")
                time.sleep(5)
                continue
            raw = resp.candidates[0].content.parts[0].inline_data.data
            if isinstance(raw, str):
                raw = base64.b64decode(raw)
            return raw
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                m = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', str(e))
                if not m:
                    m = re.search(r'retry in (\d+)', str(e))
                wait = int(m.group(1)) + 5 if m else 65
                print(f"  한도 초과, {wait}초 대기...")
                time.sleep(wait)
            else:
                raise


def detect_silences(wav_path):
    result = subprocess.run([
        "ffmpeg", "-i", str(wav_path),
        "-af", "silencedetect=n=-32dB:d=0.25",
        "-f", "null", "-"
    ], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', result.stderr)]
    ends   = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', result.stderr)]
    return list(zip(starts, ends))


def merge_silences(silences, gap=0.15):
    if not silences:
        return []
    merged = [list(silences[0])]
    for s, e in silences[1:]:
        if s - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def find_split_points(silences, total_dur):
    merged = merge_silences(silences)
    if merged and merged[-1][1] >= total_dur - 1.2:
        merged = merged[:-1]
    if len(merged) < 4:
        print(f"  경고: 무음 {len(merged)}개만 감지됨")
    return [(s + e) / 2 for s, e in merged[-4:]]


def split_to_mp3(wav_path, split_times, out_paths):
    bounds = [0.0] + split_times + [None]
    for i, mp3_path in enumerate(out_paths):
        start = bounds[i]
        end   = bounds[i + 1]
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-ss", str(start)]
        if end is not None:
            cmd += ["-to", str(end)]
        cmd += ["-codec:a", "libmp3lame", "-qscale:a", "2", str(mp3_path)]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  완료: {mp3_path.name}")


def process_set(s, folder):
    aid = s["audio_id"]
    texts = [s["passage"], s["q1"], s["q2"], s["q3"], s["q4"]]
    out_paths = [folder / f"{aid}_passage.mp3"] + [folder / f"{aid}_q{i}.mp3" for i in range(1, 5)]

    if all(p.exists() for p in out_paths):
        print(f"  건너뜀 (이미 완료)")
        return

    pcm = generate_combined(texts, VOICE)
    total_dur = len(pcm) / (SAMPLE_RATE * 2) + 0.8
    wav_path = folder / f"{aid}_combined.wav"
    wav_path.write_bytes(pcm_to_wav(pcm))

    silences = detect_silences(wav_path)
    splits = find_split_points(silences, total_dur)
    split_to_mp3(wav_path, splits, out_paths)
    wav_path.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sets = [(LOW, OUT / "low"), (MID, OUT / "mid"), (HIGH, OUT / "high")]
    total = sum(len(d) for d, _ in sets)
    idx = 0

    for data, folder in sets:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n── {folder.name.upper()} ({len(data)}세트) ──")
        for s in data:
            idx += 1
            print(f"\n[{idx}/{total}] {s['audio_id']}")
            process_set(s, folder)
            time.sleep(3)

    print(f"\n완료! → {OUT}")


if __name__ == "__main__":
    main()
