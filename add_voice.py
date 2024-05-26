from moviepy.editor import VideoFileClip, AudioFileClip
from pathlib import Path

def run(video_path: Path, audio_path: Path, output_path: Path):
    # 動画ファイルを読み込みます
    video = VideoFileClip(video_path)

    # 新しい音声ファイルを読み込みます
    new_audio = AudioFileClip(audio_path)

    # 動画に新しい音声を設定します
    video_with_new_audio = video.set_audio(new_audio)

    # 新しい動画ファイルを出力します
    video_with_new_audio.write_videofile(output_path, codec='libx264', audio_codec='aac')

    print("音声を入れ替えた動画が作成されました。")

if __name__ == "__main__":
    video_path = "/Volumes/Extreme-Pro/medicmedia/8xMO0fbz594F_medilink_movie.mp4"
    audio_path = "/Volumes/Extreme-Pro/medicmedia/audio_2.wav"
    output_path = "/Volumes/Extreme-Pro/medicmedia/translated_medilink.mp4"

    run(video_path, audio_path, output_path)