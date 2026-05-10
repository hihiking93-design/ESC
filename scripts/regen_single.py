#!/usr/bin/env python3
"""
ESC Listening Test — 단일 세트 재녹음
generate_all.py와 동일한 TTS/분리 로직, 특정 세트 1개만 생성.

사용법:
  python3 regen_single.py

출력: lt/mid/mid2_passage.mp3, mid2_q1~q4.mp3  (기존 파일 덮어쓰기)
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
SAMPLE_RATE = 24000
SILENCE_PAD = b'\x00' * int(SAMPLE_RATE * 0.8 * 2)

# lt/ 폴더는 프로젝트 루트 기준
OUT_DIR = Path(__file__).parent.parent / "lt" / "mid"

# ── 재녹음할 세트 ──────────────────────────────────────────────────
TARGET = {
    "audio_id": "mid2",
    # "주 두 번" 제거 → "월요일과 금요일 중 하루" 기준으로 일관성 유지
    "passage": "우리 회사는 이번 달부터 재택근무 제도를 도입했습니다. 직원들은 월요일과 금요일 중 하루를 선택해 재택근무를 할 수 있습니다. 단, 월말 보고 기간에는 재택근무가 제한될 수 있습니다.",
    "q1": "재택근무 제도는 언제부터 시작됩니까?",
    "q2": "이 제도에 대한 설명으로 옳은 것은?",
    "q3": "재택근무를 할 수 있는 요일 조합은?",
    "q4": "재택근무가 제한될 수 있는 경우는?",
}
# ───────────────────────────────────────────────────────────────────


def pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm + SILENCE_PAD)
    return buf.getvalue()


def generate_combined(texts: list) -> bytes:
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
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
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
            elif "403" in str(e) or "leaked" in str(e) or "PERMISSION_DENIED" in str(e):
                print(f"  키 사용 불가 ({key[:8]}...), 다음 키로 전환")
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
        print(f"  저장: {mp3_path.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    s = TARGET
    aid = s["audio_id"]

    print(f"[{aid}] TTS 생성 중...")
    print(f"  지문: {s['passage'][:40]}...")

    texts = [s["passage"], s["q1"], s["q2"], s["q3"], s["q4"]]
    out_paths = [OUT_DIR / f"{aid}_passage.mp3"] + [OUT_DIR / f"{aid}_q{i}.mp3" for i in range(1, 5)]

    pcm = generate_combined(texts)
    total_dur = len(pcm) / (SAMPLE_RATE * 2) + 0.8

    wav_path = OUT_DIR / f"{aid}_combined.wav"
    wav_path.write_bytes(pcm_to_wav(pcm))
    print(f"  WAV 저장 완료 ({total_dur:.1f}초)")

    silences = detect_silences(wav_path)
    splits = find_split_points(silences, total_dur)
    print(f"  분리 지점: {[f'{t:.2f}s' for t in splits]}")

    split_to_mp3(wav_path, splits, out_paths)
    wav_path.unlink()

    print(f"\n완료! → {OUT_DIR}")
    print("다음 단계: git add lt/mid/mid2_*.mp3 후 push → GitHub Pages 반영")


if __name__ == "__main__":
    main()
