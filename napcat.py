import requests
from config import NAPCAT_URL

class NapcatClient:

    def send_text(self, user_id: int, text: str):
        url = f"{NAPCAT_URL}/send_private_msg"
        return requests.post(url, json={
            "user_id": user_id,
            "message": text
        }).json()

    def send_image(self, user_id: int, image_url: str):
        url = f"{NAPCAT_URL}/send_private_msg"
        msg = f"[CQ:image,file={image_url}]"
        return requests.post(url, json={
            "user_id": user_id,
            "message": msg
        }).json()

    def send_video(self, user_id: int, video_url: str):
        url = f"{NAPCAT_URL}/send_private_msg"
        msg = f"[CQ:video,file={video_url}]"
        return requests.post(url, json={
            "user_id": user_id,
            "message": msg
        }).json()

    def send_voice(self, user_id: int, voice_url: str):
        url = f"{NAPCAT_URL}/send_private_msg"
        msg = f"[CQ:record,file={voice_url}]"
        return requests.post(url, json={
            "user_id": user_id,
            "message": msg
        }).json()


napcat = NapcatClient()