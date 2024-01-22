import multiprocessing
import os
import re
from tqdm import tqdm
from os.path import exists  # Needs to be imported specifically
from typing import Final
from typing import Tuple, Any, Dict

import ffmpeg
from PIL import Image
from rich.console import Console
from rich.progress import track

from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.thumbnail import create_thumbnail
from utils.videos import save_data
from utils.playback_control import video_playback_control
from utils import settings

from video_creation.final_video_resources import ProgressFfmpeg
from video_creation.final_video_resources import prepare_background
from video_creation.final_video_resources import merge_background_audio
from video_creation.final_video_resources import name_normalize

from video_creation.logo_outro import *

console = Console()

def make_final_video(
    number_of_clips: int,
    length: int,
    poll_data: dict,
    background_config: Dict[str, Tuple],
):
    """Gathers audio clips, gathers all screenshots, stitches them together and saves the final video to assets/temp
    Args:
        number_of_clips (int): Index to end at when going through the screenshots'
        length (int): Length of the video
        reddit_obj (dict): The reddit object that contains the posts to read.
        background_config (Tuple[str, str, str, Any]): The background config to use.
    """

    console.log(f"[bold blue] Length parameter received in make_final_video: {length} seconds")

    console.log("[bold blue] Poll Data: ",poll_data)

    poll_id = poll_data["pollId"]

    # settings values
    W: Final[int] = int(settings.config["settings"]["resolution_w"])
    H: Final[int] = int(settings.config["settings"]["resolution_h"])

    opacity = settings.config["settings"]["opacity"]

    allowOnlyTTSFolder: bool = (
        settings.config["settings"]["background"]["enable_extra_audio"]
        and settings.config["settings"]["background"]["background_audio_volume"] != 0
    )

    print_step("Creating the final video 🎥")

    background_clip = ffmpeg.input(prepare_background(poll_id, W=W, H=H))
    screenshot_width = int((W * 45) // 100)

    # Collect audio clips
    audio_clips = []
    audio_clips_durations = []

    poll_audio_path = f"assets/temp/{poll_id}/mp3/poll.mp3"
    if os.path.exists(poll_audio_path):
        audio_clips.append(ffmpeg.input(poll_audio_path))
        audio_clips_durations.append(float(ffmpeg.probe(poll_audio_path)["format"]["duration"]))

    answered_poll_audio_path = f"assets/video-resources/answered-poll.mp3"
    if os.path.exists(answered_poll_audio_path):
        audio_clips.append(ffmpeg.input(answered_poll_audio_path))
        audio_clips_durations.append(float(ffmpeg.probe(answered_poll_audio_path)["format"]["duration"]))

    for i in range(number_of_clips):
        audio_path = f"assets/temp/{poll_id}/mp3/comment{i}.mp3"
        if os.path.exists(audio_path):
            audio_clips.append(ffmpeg.input(audio_path))
            audio_clips_durations.append(float(ffmpeg.probe(audio_path)["format"]["duration"]))
        else:
            print(f"Warning: Audio file not found: {audio_path}")


    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(audio_concat, f"assets/temp/{poll_id}/audio.mp3", **{"b:a": "192k"}).overwrite_output().run(quiet=True)

    audio = ffmpeg.input(f"assets/temp/{poll_id}/audio.mp3")
    final_audio = merge_background_audio(audio, poll_id)

    # Duration of the fade-out effect in seconds
    fade_duration = 3

    # Apply the audio fade-out effect at the end of the audio track
    final_audio = final_audio.filter('afade', type='out', start_time=length - fade_duration, duration=fade_duration)

    # Calculate total video length
    total_video_length = sum(audio_clips_durations)
    length = total_video_length
    
    console.log(f"[bold blue] Total Length: {length} seconds")
    console.log(f"[bold blue] Total Video Length without outro: {total_video_length} seconds")

    image_clips = list()

    image_clips.insert(
        0,
        ffmpeg.input(f"assets/temp/{poll_id}/png/poll/poll-question.png")["v"].filter(
            "scale", screenshot_width, -1
        ),
    )

    poll_image_path = f"assets/temp/{poll_id}/png/poll/poll.png"

    image_clips.append(ffmpeg.input(poll_image_path)["v"].filter(
            "scale", screenshot_width, -1
        ),
    )

    # # Overlay for poll.png
    # current_time = 0
    # poll_image_path = f"assets/temp/{poll_id}/png/poll/poll.png"
    # if os.path.exists(poll_image_path):
    #     poll_image_clip = ffmpeg.input(poll_image_path)["v"].filter("scale", screenshot_width, -1)
    #     background_clip = background_clip.overlay(
    #         poll_image_clip.filter("colorchannelmixer", aa=opacity),
    #         enable=f"between(t,{current_time},{current_time + 3})",  # 3 seconds for answered-poll.mp3
    #         x="(main_w-overlay_w)/2",
    #         y="(main_h-overlay_h)/2"
    #     )
    #     current_time += answered_poll_duration  # Duration for answered-poll.mp3

    audio_length = enumerate(audio_clips_durations)
    console.log("[bold green] i value: ", audio_length)

    current_time = 0
    # Overlay images corresponding to audio clips
    for i, duration in audio_length:
        console.log("[bold green] i value: ", i, "Duration: ", {duration})
        # image_path = f"assets/temp/{poll_id}/png/poll/poll-question.png" if i == 0 else f"assets/temp/{poll_id}/png/comment/comment{i-1}.png"

        # Select the appropriate image path based on the index
        if i == 0:
            image_path = f"assets/temp/{poll_id}/png/poll/poll-question.png"
        elif i == 1:
            image_path = f"assets/temp/{poll_id}/png/poll/poll.png"
        else:
            image_path = f"assets/temp/{poll_id}/png/comment/comment{i-2}.png"


        if os.path.exists(image_path):
            image_clip = ffmpeg.input(image_path)["v"].filter("scale", screenshot_width, -1)
            image_overlay = image_clip.filter("colorchannelmixer", aa=opacity) if i > 1 else image_clip
            background_clip = background_clip.overlay(
                image_overlay,
                enable=f"between(t,{current_time},{current_time + duration})",
                x="(main_w-overlay_w)/2",
                y="(main_h-overlay_h)/2"
            )
            print(f"Image overlay added: {image_path} (Start: {current_time}s, Duration: {duration}s)")
        else:
            print(f"Warning: Image file not found: {image_path}")
        current_time += duration
            
    poll_title = poll_data["question"]
    title_thumb = poll_title[:50] 

    filename = f"{name_normalize(poll_title)[:251]}"
    subreddit = settings.config["reddit"]["thread"]["subreddit"]

    if not exists(f"./results/{subreddit}"):
        print_substep("The 'results' folder could not be found so it was automatically created.")
        os.makedirs(f"./results/{subreddit}")

    if not exists(f"./results/{subreddit}/OnlyTTS") and allowOnlyTTSFolder:
        print_substep("The 'OnlyTTS' folder could not be found so it was automatically created.")
        os.makedirs(f"./results/{subreddit}/OnlyTTS")

    # create a thumbnail for the video
    settingsbackground = settings.config["settings"]["background"]

    if settingsbackground["background_thumbnail"]:
        if not exists(f"./results/{subreddit}/thumbnails"):
            print_substep(
                "The 'results/thumbnails' folder could not be found so it was automatically created."
            )
            os.makedirs(f"./results/{subreddit}/thumbnails")
        # get the first file with the .png extension from assets/backgrounds and use it as a background for the thumbnail
        first_image = next(
            (file for file in os.listdir("assets/backgrounds") if file.endswith(".png")),
            None,
        )
        if first_image is None:
            print_substep("No png files found in assets/backgrounds", "red")

        else:
            font_family = settingsbackground["background_thumbnail_font_family"]
            font_size = settingsbackground["background_thumbnail_font_size"]
            font_color = settingsbackground["background_thumbnail_font_color"]
            thumbnail = Image.open(f"assets/backgrounds/{first_image}")
            width, height = thumbnail.size
            thumbnailSave = create_thumbnail(
                thumbnail,
                font_family,
                font_size,
                font_color,
                width,
                height,
                title_thumb,
            )
            thumbnailSave.save(f"./assets/temp/{poll_id}/thumbnail.png")
            print_substep(f"Thumbnail - Building Thumbnail in assets/temp/{poll_id}/thumbnail.png")

    text = f"Background by {background_config['video'][2]}"
    background_clip = ffmpeg.drawtext(
        background_clip,
        text=text,
        x=f"(w-text_w)",
        y=f"(h-text_h)",
        fontsize=5,
        fontcolor="White",
        fontfile=os.path.join("fonts", "Roboto-Regular.ttf"),
    )
    background_clip = background_clip.filter("scale", W, H)
    print_step("Rendering the video 🎥")

    from tqdm import tqdm

    pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")

    def on_update_example(progress) -> None:
        status = round(progress * 100, 2)
        old_percentage = pbar.n
        pbar.update(status - old_percentage)

    defaultPath = f"results/{subreddit}"
    with ProgressFfmpeg(total_video_length, on_update_example) as progress:
        path = defaultPath + f"/{filename}"
        path = (
            path[:251] + ".mp4"
        )  # Prevent a error by limiting the path length, do not change this.
        try:
            ffmpeg.output(
                background_clip, 
                final_audio,
                path,
                f="mp4",
                **{
                    "c:v": "h264",
                    "b:v": "20M",
                    "b:a": "192k",
                    "threads": multiprocessing.cpu_count(),
                },
            ).overwrite_output().global_args("-progress", progress.output_file.name).run(
                quiet=True,
                overwrite_output=True,
                capture_stdout=False,
                capture_stderr=False,
            )
        except ffmpeg.Error as e:
            print(e.stderr.decode("utf8"))
            exit(1)
    old_percentage = pbar.n
    pbar.update(100 - old_percentage)
    if allowOnlyTTSFolder:
        path = defaultPath + f"/OnlyTTS/{filename}"
        path = (
            path[:251] + ".mp4"
        )  # Prevent a error by limiting the path length, do not change this.
        print_step("Rendering the Only TTS Video 🎥")
        with ProgressFfmpeg(total_video_length, on_update_example) as progress:
            try:
                ffmpeg.output(
                    background_clip,
                    audio,
                    path,
                    f="mp4",
                    **{
                        "c:v": "h264",
                        "b:v": "20M",
                        "b:a": "192k",
                        "threads": multiprocessing.cpu_count(),
                    },
                ).overwrite_output().global_args("-progress", progress.output_file.name).run(
                    quiet=True,
                    overwrite_output=True,
                    capture_stdout=False,
                    capture_stderr=False,
                )
            except ffmpeg.Error as e:
                print(e.stderr.decode("utf8"))
                exit(1)

        old_percentage = pbar.n
        pbar.update(100 - old_percentage)
    pbar.close()
    # save_data(subreddit, filename + ".mp4", poll_title, idx, background_config["video"][2])
    save_data(subreddit, filename + ".mp4", poll_title, poll_id, background_config["video"][2])


    video_path = path
    slowed_video_path = f"assets/temp/{poll_id}/slowed_video.mp4"   # Path for the slowed-down video

    # Call the function to slow down the video
    video_playback_control(video_path, slowed_video_path)

    # Path to the outro video and logo
    # outro_video_path = "assets/video-resources/outro.mp4"
    logo_gif_path = "assets/video-resources/logo_animation_1.gif"

    # Paths for intermediate videos
    audio_path = f"assets/temp/{poll_id}/extracted_audio.aac"
    processed_video_path = f"assets/temp/{poll_id}/processed_video.mp4" 
    intermediate_output_path = f"assets/temp/{poll_id}/intermediate_video.mp4" 
    reencoded_outro_video_path = f"assets/video-resources/reencoded_outro_video copy.mp4"
    reencoded_main_video_path = f"assets/temp/{poll_id}/reencoded_main_video.mp4"

    # Final output path
    final_output_path = f"./results/{subreddit}/finalvideo/finalvideo_{poll_title}.mp4"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(final_output_path), exist_ok=True)

    # Extract audio from the original video
    extract_audio(slowed_video_path, audio_path)

    # Process the video frames (overlay GIF)
    overlay_gif_on_video(slowed_video_path, logo_gif_path, processed_video_path)

    # Combine the processed video with the extracted audio
    combine_video_audio(processed_video_path, audio_path, intermediate_output_path)

    # Re-encode the videos to match main video properties
    reencode_video(intermediate_output_path, reencoded_main_video_path)
    # reencode_video(outro_video_path, reencoded_outro_video_path)

    concatenate_videos(intermediate_output_path, reencoded_outro_video_path, final_output_path)

    print_step("Removing temporary files 🗑")
    cleanups = cleanup(poll_id)
    print_substep(f"Removed {cleanups} temporary files 🗑")
    print_step("Done! 🎉 The video is in the results folder 📁")