import tempfile
from pathlib import Path
import json
from datetime import datetime
import ast

from openai import OpenAI
from pydub import AudioSegment

from .config_loader import load_config

OPENAI_API_KEY = load_config("config.toml")["openai"]["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)


def translate_to_en_json(audio_file_path):
   
    audio_file= open(audio_file_path, "rb")
    translation_json = client.audio.translations.create(
    model="whisper-1", 
    file=audio_file,
    response_format="verbose_json",
    timestamp_granularities=["word"]
    )

    print(translation_json)


def translate_to_en(audio_file_path):
    
    audio_file= open(audio_file_path, "rb")
    translation = client.audio.translations.create(
    model="whisper-1", 
    file=audio_file,
    response_format="text"
    )

    print(translation)


def speech_to_text(audio_file_path):
    
    audio_file= open(audio_file_path, "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )

    print(transcription.text)


def speech_to_text_json(audio_file_path) -> list:
    audio_file= open(audio_file_path, "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    language="ja",
    file=audio_file,
    response_format="verbose_json",
    )
    print(transcription.segments)

    # 現在時刻でファイル名を作成
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"whisper_result_{current_datetime}.json"

    # JSONファイルに保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(transcription.segments, f, ensure_ascii=False, indent=4)

    print(f"Data saved to {filename}")

    return transcription.segments


def translation_with_gpt4o(text_list: list):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": 'これはある動画の音声部分を書き起こした配列です。この配列の文脈を理解したうえで、[{"id":0, "en-text": {translated_text}}]のリスト型で翻訳を行ってください。基本的に要素一つに対して一つずつ翻訳を行い、絶対に配列の長さが元のデータと同じになるようにしてください。配列の長さの調節が難しい場合は空の要素を入れても良いので絶対に同じにしてください'},
            {"role": "user", "content": f"{text_list}"}
        ],
        temperature=0.1,
    )
    
    output = completion.choices[0].message.content
    translated_text = json.loads(output)  # JSONの形式に適合するようにシングルクォートをダブルクォートに置き換える
        
    return translated_text


def translate_to_en(whisper_result):
    # 各セグメントの日本語テキストを抽出
    #text_list = [{"id": item["id"], "text": item["text"]} for item in whisper_result]

    # GPT-4を使って日本語テキストを英語に翻訳
    english_texts = translation_with_gpt4o(whisper_result)
    print(english_texts)

    # 新しいセグメントリストを作成
    new_segments = []
    for segment, en_text in zip(whisper_result, english_texts):
        en_text = next((item['en-text'] for item in english_texts if item['id'] == segment['id']), None)
        new_segment = {
            'id': segment['id'],
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['text'],
            'en_text': en_text
        }
        new_segments.append(new_segment)

    return new_segments

def text_to_speech(text):
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file_path = Path(temp_file.name)

            # OpenAIのAPIを使用して音声ファイルを生成
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )

            # 生成された音声を一時ファイルに保存
            response.stream_to_file(temp_file_path)
        
        # 保存された音声ファイルを読み込んでAudioSegmentオブジェクトを作成
        audio_segment = AudioSegment.from_file(temp_file_path, format="mp3")
        
        # 一時ファイルを削除（不要ならばこの行をコメントアウト）
        temp_file_path.unlink()
        print(f"Speech generated for text: {text}")

        return audio_segment
    except Exception as e:
        print(f"Error generating speech for text: {text}\n{e}")
        return AudioSegment.silent(duration=1000)  # エラーが発生した場合は1秒の無音を返す

def make_audiofile(segments):
    full_audio = AudioSegment.silent(duration=0)  # 結合された全音声の初期化

    for i, segment in enumerate(segments):
        start_time = segment["start"] * 1000  # 開始時間をミリ秒に変換
        text_en = segment["en_text"]

        # 英語のテキストを音声に変換
        audio_segment = text_to_speech(text_en)

        # 無音区間を追加してタイミングを合わせる
        if full_audio.duration_seconds * 1000 < start_time:
            silence_duration = start_time - full_audio.duration_seconds * 1000
            full_audio += AudioSegment.silent(duration=silence_duration)

        # 英語音声を結合
        full_audio += audio_segment

        # 次のセグメントの開始時間までの無音を追加
        if i < len(segments) - 1:
            next_start_time = segments[i + 1]["start"] * 1000
            if full_audio.duration_seconds * 1000 < next_start_time:
                silence_duration = next_start_time - full_audio.duration_seconds * 1000
                full_audio += AudioSegment.silent(duration=silence_duration)

    # 最終的な音声ファイルとして出力
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"translated_audio_{current_datetime}.mp3"
    full_audio.export(filename, format="mp3")
    print(f"Audio file saved as: {filename}")

if __name__ == "__main__":

    audio_file_path = "/Volumes/Extreme Pro/medicmedia/medilink_audio.m4a"
    #whisper_result = speech_to_text_json(audio_file_path)

    with open('./output/whisper_result.json', 'r', encoding='utf-8') as f:
        whisper_result = json.load(f)

    new_segments = translate_to_en(whisper_result)
    make_audiofile(new_segments)
    

