import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import requests

url_base = "https://huggingface.co/IAHispano/Applio/resolve/main/Resources"

linux_executables_list = [("formant/", ["stftpitchshift"])]
executables_list = [
    ("", ["ffmpeg.exe", "ffprobe.exe"]),
    ("formant/", ["stftpitchshift.exe"]),
]

folder_mapping_list = {
    "formant/": "main/rvc/engine/models/formant/",
}


def get_file_size_if_missing(file_list, custom_url_base=None):
    """
    Calculate the total size of files to be downloaded only if they do not exist locally.
    """
    base = custom_url_base if custom_url_base else url_base
    total_size = 0
    for remote_folder, files in file_list:
        local_folder = folder_mapping_list.get(remote_folder, "")
        for file in files:
            destination_path = os.path.join(local_folder, file)
            if not os.path.exists(destination_path):
                url = f"{base}/{file}"
                response = requests.head(url)
                total_size += int(response.headers.get("content-length", 0))
    return total_size


def download_file(url, destination_path, global_bar):
    """
    Download a file from the given URL to the specified destination path,
    updating the global progress bar as data is downloaded.
    """

    dir_name = os.path.dirname(destination_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    response = requests.get(url, stream=True)
    block_size = 1024
    with open(destination_path, "wb") as file:
        for data in response.iter_content(block_size):
            file.write(data)
            global_bar.update(len(data))


def download_mapping_files(file_mapping_list, global_bar, custom_url_base=None):
    """
    Download all files in the provided file mapping list using a thread pool executor,
    and update the global progress bar as downloads progress.
    """
    base = custom_url_base if custom_url_base else url_base
    with ThreadPoolExecutor() as executor:
        futures = []
        for remote_folder, file_list in file_mapping_list:
            local_folder = folder_mapping_list.get(remote_folder, "")
            for file in file_list:
                destination_path = os.path.join(local_folder, file)
                if not os.path.exists(destination_path):
                    url = f"{base}/{file}"
                    futures.append(
                        executor.submit(
                            download_file, url, destination_path, global_bar
                        )
                    )
        for future in futures:
            future.result()


def calculate_total_size(exe):
    """
    Calculate the total size of all files to be downloaded based on selected categories.
    """
    total_size = 0
    if exe:
        total_size += get_file_size_if_missing(
            executables_list if os.name == "nt" else linux_executables_list
        )
    return total_size


def prequisites_download_pipeline(exe):
    """
    Manage the download pipeline for different categories of files.
    """
    total_size = calculate_total_size(exe)

    if total_size > 0:
        with tqdm(
            total=total_size, unit="iB", unit_scale=True, desc="Downloading all files", ncols=80, colour='MAGENTA', mininterval=0.5
        ) as global_bar:
            if exe:
                download_mapping_files(
                    executables_list if os.name == "nt" else linux_executables_list,
                    global_bar,
                )
    else:
        pass


if __name__ == "__main__":
    prequisites_download_pipeline(False)
