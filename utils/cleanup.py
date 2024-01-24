import os
from os.path import exists
import shutil


def _listdir(d):  # listdir with full path
    return [os.path.join(d, f) for f in os.listdir(d)]


def cleanup(poll_id) -> int:
    """Deletes all temporary assets in assets/temp

    Returns:
        int: How many files were deleted
    """
    directory = f"../assets/temp/{poll_id}/"
    if exists(directory):
        shutil.rmtree(directory)

        return 1


def cleanup_after_video_creation(poll_id: str, subreddit: str):
    try:
        # Delete the poll_id folder inside assets/temp
        temp_poll_folder = os.path.join("assets", "temp", poll_id)
        if os.path.exists(temp_poll_folder):
            shutil.rmtree(temp_poll_folder)
            print(f"Deleted temporary poll folder: {temp_poll_folder}")

        # Delete files in results/{subreddit} except for the finalvideo folder
        results_folder = os.path.join("results", subreddit)
        final_video_folder = os.path.join(results_folder, "finalvideo")

        for item in os.listdir(results_folder):
            item_path = os.path.join(results_folder, item)
            if os.path.isfile(item_path) or (os.path.isdir(item_path) and item_path != final_video_folder):
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f"Deleted: {item_path}")

        print("Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")