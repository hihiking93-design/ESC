#!/usr/bin/env python3
"""
1세트를 하나의 TTS 호출로 생성 → 무음 구간에서 5개 파일로 분리
"""
import base64, subprocess, wave, io, re, time
from itertools import cycle
from pathlib import Path
from google import genai
from google.genai import types

API_KEYS = [
    "AIzaSyDPWrOESfxhnYqpuudc7UhhnU1rmX4kL3U",
    "AIzaSyAhyHM-ZnNPPCf_ktpmmYStbiFJO4my6E8",
    "AIzaSyCkNpn58hvlqbZP9UR6iFuqQuEC75kMKD0",
    "AIzaSyCsjxRlB4kxV1FB2n3ZTycRMj80-yJZyB8",
    "AIzaSyDYSoMN0V5UB9l812nNBEqEDFV12xP7kaQ",
]
key_cycle = cycle(API_KEYS)
MODEL   = "gemini-2.5-flash-preview-tts"
VOICE   = "Kore"
OUT     = Path("output/low")
OUT.mkdir(parents=True, exist_ok=True)

# low1 텍스트
PASSAGE = "빨간 옷을 입은 목수가 다섯 개의 못과 두 개의 망치를 들고 보라색 울타리를 고치고 있습니다. 초록색 긴 생머리에 연두색 원피스를 입은 목수의 아내가 옥수수 여덟 개와 감자 일곱 개를 쪄서 새참으로 나누어 먹습니다."
Q1 = "목수가 입은 옷의 색은?"
Q2 = "목수가 고치는 울타리의 색은?"
Q3 = "목수의 아내가 찐 옥수수의 수는?"
Q4 = "목수의 아내 원피스 색은?"

LABELS = ["low1_passage", "low1_q1", "low1_q2", "low1_q3", "low1_q4"]

COMBINED = "  ".join([PASSAGE, Q1, Q2, Q3, Q4])
PROMPT   = f"다음 텍스트를 그대로 읽어주세요: {COMBINED}"

SAMPLE_RATE   = 24000
SILENCE_PAD   = b'\x00' * int(SAMPLE_RATE * 0.8 * 2)  # 끝 0.8초 패딩

def generate_combined():
    print("TTS 생성 중 (1회 호출)...")
    for attempt in range(20):
        key = next(key_cycle)
        client = genai.Client(api_key=key)
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=PROMPT,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                        ),
                        language_code="ko-KR",
                    ),
                ),
            )
            if not resp.candidates or not resp.candidates[0].content:
                print("  빈 응답, 재시도...")
                time.sleep(3)
                continue
            raw = resp.candidates[0].content.parts[0].inline_data.data
            if isinstance(raw, str):
                raw = base64.b64decode(raw)
            return raw
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"  키 교체 후 재시도...")
                time.sleep(2)
            else:
                raise
    print("모든 키 소진, 60초 대기...")
    time.sleep(60)
    return generate_combined()

def pcm_to_wav(pcm):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm + SILENCE_PAD)
    return buf.getvalue()

def detect_silences(wav_path, min_duration=0.25, noise_floor=-32):
    """ffmpeg으로 무음 구간 감지 → [(start, end), ...] 반환"""
    result = subprocess.run([
        "ffmpeg", "-i", str(wav_path),
        "-af", f"silencedetect=n={noise_floor}dB:d={min_duration}",
        "-f", "null", "-"
    ], capture_output=True, text=True)

    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', result.stderr)]
    ends   = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', result.stderr)]

    silences = list(zip(starts, ends))
    return silences

def merge_silences(silences, gap=0.15):
    """간격이 gap초 이하인 인접 무음 구간을 하나로 합침"""
    if not silences:
        return []
    merged = [list(silences[0])]
    for s, e in silences[1:]:
        if s - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]

def find_split_points(silences, n_splits=4, total_dur=None):
    """뒤에서부터 n개 무음 구간의 중간 지점을 분리 기준으로 사용"""
    merged = merge_silences(silences)

    # 끝 패딩 무음 제거 (마지막 무음이 총 길이 1초 이내에서 끝나면)
    if total_dur and merged and merged[-1][1] >= total_dur - 1.2:
        merged = merged[:-1]

    if len(merged) < n_splits:
        print(f"경고: 무음 구간이 {len(merged)}개만 감지됨 (필요: {n_splits})")

    print(f"  합쳐진 무음: {len(merged)}개")
    for s, e in merged:
        print(f"    {s:.2f}s ~ {e:.2f}s  (길이: {e-s:.2f}s)")

    top = merged[-n_splits:]
    midpoints = [(s+e)/2 for s, e in top]
    return midpoints

def split_to_mp3(wav_path, split_times, labels):
    bounds = [0.0] + split_times + [None]
    out_paths = []
    for i, label in enumerate(labels):
        mp3_path = OUT / f"{label}.mp3"
        start = bounds[i]
        end   = bounds[i+1]

        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-ss", str(start)]
        if end is not None:
            cmd += ["-to", str(end)]
        cmd += ["-codec:a", "libmp3lame", "-qscale:a", "2", str(mp3_path)]
        subprocess.run(cmd, capture_output=True, check=True)

        dur = f"~ {end-start:.1f}초" if end else ""
        print(f"  저장: {mp3_path.name}  [{start:.2f}s → {str(end)+'s' if end else '끝'}] {dur}")
        out_paths.append(mp3_path)
    return out_paths

# ── 실행 ──────────────────────────────────────────────────────
pcm = generate_combined()
print(f"생성 완료 ({len(pcm)//SAMPLE_RATE//2}초 분량)")

combined_wav = OUT / "combined_low1.wav"
combined_wav.write_bytes(pcm_to_wav(pcm))

print("\n무음 구간 감지 중...")
silences = detect_silences(combined_wav)
print(f"감지된 무음: {len(silences)}개")
for s, e in silences:
    print(f"  {s:.2f}s ~ {e:.2f}s  (길이: {e-s:.2f}s)")

total_dur = len(pcm) / (SAMPLE_RATE * 2) + 0.8  # PCM 길이 + 패딩
splits = find_split_points(silences, n_splits=4, total_dur=total_dur)
print(f"\n분리 기준점: {[f'{t:.2f}s' for t in splits]}")

print("\n파일 분리 중...")
files = split_to_mp3(combined_wav, splits, LABELS)

combined_wav.unlink()
print("\n재생 시작!")
for f in files:
    print(f"▶ {f.name}")
    subprocess.run(["afplay", str(f)])

print("\n완료!")
