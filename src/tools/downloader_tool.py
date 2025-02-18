import os

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()


class DownloaderTool(BaseTool):
    name: str = "downloader"
    description: str = "Downloads a file from a given link."

    def _run(self, download_links: list[str] | str, filenames: list[str] | str, save_path: str) -> dict:

        if isinstance(download_links, str):
            download_links = [download_links]
        if isinstance(filenames, str):
            filenames = [filenames]

        # download_links ve filenames aynı uzunlukta olmalı
        if len(download_links) != len(filenames):
            raise ValueError("The number of download_links must match the number of filenames.")

        os.makedirs(save_path, exist_ok=True)

        results = []
        for link, filename in zip(download_links, filenames):
            try:
                # Video dosyasını indir
                response = requests.get(link, stream=True)
                if response.status_code != 200:
                    raise Exception(f"Failed to download file: {response.status_code}")

                # Dosya yolunu oluştur
                file_path = os.path.join(save_path, filename)

                # Dosyayı kaydet
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=128):
                        file.write(chunk)

                results.append({"link": link, "status": "success", "path": file_path})
            except Exception as e:
                results.append({"link": link, "status": "failed", "error": str(e)})

        return {"downloads": results}

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async functionality is not implemented yet.")
