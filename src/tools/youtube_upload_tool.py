import os
import shutil

from crewai.tools import BaseTool
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from pydantic import Field, BaseModel
from pydub import AudioSegment

import google_auth_httplib2
import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = 'token.json'


class YoutubeUploadTool(BaseTool):
    name: str = "youtube_upload_tool"
    description: str = "Upload videos to YouTube"

    def authenticate_youtube(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)

        # Load client secrets file, put the path of your file
        client_secrets_file = "resource/youtube-client.json"

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, SCOPES)
        credentials = flow.run_local_server()

        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials)

        return youtube

    def upload_video(self, youtube):
        request_body = {
            "snippet": {
                "categoryId": "22",
                "title": "Uploaded from Python",
                "description": "This is the most awsome description ever",
                "tags": ["test", "python", "api"]
            },
            "status": {
                "privacyStatus": "private"
            }
        }

        # put the path of the video that you want to upload
        media_file = "output/done/1738321603.mp4"

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=googleapiclient.http.MediaFileUpload(media_file, chunksize=-1, resumable=True)
        )

        response = None

        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload {int(status.progress() * 100)}%")

            print(f"Video uploaded with ID: {response['id']}")

    def _run(self) -> dict:
        youtube = self.authenticate_youtube()
        self.upload_video(youtube)
        return {"status": "success"}
