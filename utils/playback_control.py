import ffmpeg
from ffmpeg import input, output, run
import os

def video_playback_control(input_video_path, output_video_path, playback_speed=1.0):

    # Create separate input streams for video and audio
    video_input = ffmpeg.input(input_video_path)
    audio_input = ffmpeg.input(input_video_path)

    # Apply the setpts filter to slow down the video
    slowed_video = video_input.filter('setpts', f'{1/playback_speed}*PTS')

    # Apply the atempo filter to adjust the speed of the audio
    # The atempo filter requires a speed value between 0.5 and 2.0
    # For values outside this range, the filter needs to be applied multiple times
    if playback_speed < 0.5:
        slowed_audio = audio_input.audio.filter('atempo', 0.5).filter('atempo', playback_speed / 0.5)
    elif playback_speed > 2.0:
        slowed_audio = audio_input.audio.filter('atempo', 2.0).filter('atempo', playback_speed / 2.0)
    else:
        slowed_audio = audio_input.audio.filter('atempo', playback_speed)

    # Combine the slowed video and audio, and output to the specified file
    ffmpeg.output(slowed_video, slowed_audio, output_video_path, acodec='aac').run(quiet=True)
