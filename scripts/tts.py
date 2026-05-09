#!/usr/bin/env python3
"""
Gemini TTS 자동화 스크립트
텍스트 파일을 읽어서 WAV 오디오 파일로 변환합니다.

사용법:
  python tts.py input.txt              # 전체 파일을 하나의 오디오로
  python tts.py input.txt --split      # 빈 줄 기준으로 분리해서 여러 파일로
  python tts.py input.txt --voice Kore # 목소리 지정
"""

import argparse
import base64
import os
import struct
import sys
import wave
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("패키지 설치 필요: pip install google-genai")
    sys.exit(1)

# 사용 가능한 목소리 목록 (한국어 지원)
VOICES = [
    "Aoede", "Charon", "Fenrir", "Kore", "Leda",
    "Orus", "Puck", "Schedar", "Sulafat", "Zephyr",
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam",
    "Aoede", "Autonoe", "Callirrhoe", "Despina", "Enceladus",
    "Erinome", "Gacrux", "Iocaste", "Kore", "Laomedeia",
    "Leda", "Meissa", "Mimas", "Mintaka", "Nashira",
    "Puck", "Pulcherrima", "Rasalas", "Sadachbia", "Sadaltager",
    "Schedar", "Sulafat", "Umbriel", "Vindemiatrix", "Wasat",
    "Zubenelgenubi",
]

MODEL = "gemini-2.5-flash-preview-tts"


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """PCM raw 데이터를 WAV 형식으로 변환"""
    import io
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def generate_tts(client, text: str, voice: str, language_code: str) -> bytes:
    """텍스트를 음성으로 변환하고 WAV bytes 반환"""
    response = client.models.generate_content(
        model=MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                ),
                language_code=language_code,
            ),
        ),
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data
    # inline_data.data는 이미 bytes이거나 base64 문자열일 수 있음
    if isinstance(audio_data, str):
        audio_data = base64.b64decode(audio_data)

    return pcm_to_wav(audio_data)


def split_text(text: str) -> list[str]:
    """빈 줄 기준으로 텍스트 분리, 각 청크는 빈 문자열 제거"""
    chunks = []
    current = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                chunks.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def main():
    parser = argparse.ArgumentParser(description="Gemini TTS 자동화")
    parser.add_argument("input", help="입력 텍스트 파일 (.txt)")
    parser.add_argument("--split", action="store_true", help="빈 줄 기준으로 분리해서 여러 파일 생성")
    parser.add_argument("--voice", default="Kore", help=f"목소리 선택 (기본: Kore). 선택지: {', '.join(VOICES[:10])}...")
    parser.add_argument("--lang", default="ko-KR", help="언어 코드 (기본: ko-KR, 영어: en-US)")
    parser.add_argument("--output-dir", default=None, help="출력 폴더 (기본: 입력 파일과 같은 폴더)")
    parser.add_argument("--api-key", default=None, help="Gemini API 키 (없으면 GEMINI_API_KEY 환경변수 사용)")
    args = parser.parse_args()

    # API 키 설정
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("오류: API 키가 필요합니다.")
        print("  방법 1: --api-key YOUR_KEY 옵션 사용")
        print("  방법 2: export GEMINI_API_KEY=YOUR_KEY 환경변수 설정")
        print("\nAPI 키 발급: https://aistudio.google.com/apikey")
        sys.exit(1)

    # 입력 파일 확인
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        print("오류: 파일이 비어 있습니다.")
        sys.exit(1)

    # 출력 폴더
    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gemini 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    stem = input_path.stem

    if args.split:
        chunks = split_text(text)
        print(f"총 {len(chunks)}개 청크로 분리됨 (목소리: {args.voice}, 언어: {args.lang})\n")
        for i, chunk in enumerate(chunks, 1):
            preview = chunk[:50].replace("\n", " ")
            print(f"[{i}/{len(chunks)}] 변환 중: \"{preview}...\"")
            wav = generate_tts(client, chunk, args.voice, args.lang)
            out_path = output_dir / f"{stem}_{i:03d}.wav"
            out_path.write_bytes(wav)
            print(f"         저장됨: {out_path}")
            if i < len(chunks):
                time.sleep(0.5)  # API rate limit 방지
    else:
        print(f"변환 중... (목소리: {args.voice}, 언어: {args.lang})")
        wav = generate_tts(client, text, args.voice, args.lang)
        out_path = output_dir / f"{stem}.wav"
        out_path.write_bytes(wav)
        print(f"저장됨: {out_path}")

    print("\n완료!")


if __name__ == "__main__":
    main()
