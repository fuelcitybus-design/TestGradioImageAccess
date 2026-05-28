from fastapi import FastAPI

app = FastAPI()

import gradio as gr
import requests
from requests.auth import HTTPBasicAuth
import os

# Replace with your App Service details
APP_NAME = "oil-tank-refueling"   # e.g. oil-tank-refueling-e8a5atdqg9fnh2et
USERNAME = "oil-tank-refueling\$oil-tank-refueling"
PASSWORD = "xrzqs40NcHhiqk1c2ukoTc4wTSoHHgFy77MjzRzsXlgkusz8uqhnd6KZ3tsR"

BASE_URL = f"https://{APP_NAME}.scm.azurewebsites.net/api/vfs/home/"

auth = HTTPBasicAuth(USERNAME, PASSWORD)

def upload_to_kudu(image_path):
    file_name = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        r = requests.put(BASE_URL + file_name, data=f, auth=auth)
    if r.status_code in (200, 201):
        return f"✅ Uploaded {file_name} successfully"
    else:
        return f"❌ Upload failed: {r.status_code} {r.text}"

def list_images():
    r = requests.get(BASE_URL, auth=auth)
    if r.status_code == 200:
        files = [f["name"] for f in r.json() if f["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
        return files
    return ["Error listing files"]

def get_image(file_name):
    r = requests.get(BASE_URL + file_name, auth=auth)
    if r.status_code == 200:
        temp_path = f"/tmp/{file_name}"
        with open(temp_path, "wb") as f:
            f.write(r.content)
        return temp_path
    return None

with gr.Blocks() as demo:
    gr.Markdown("## Upload Images to Azure App Service (Kudu Storage)")

    with gr.Tab("Upload"):
        img_input = gr.Image(type="filepath", label="Select an image")
        upload_btn = gr.Button("Upload to Kudu (/home)")
        upload_output = gr.Textbox(label="Result")
        upload_btn.click(upload_to_kudu, inputs=img_input, outputs=upload_output)

    with gr.Tab("Browse"):
        list_btn = gr.Button("List Images in /home")
        file_list = gr.Dropdown(label="Saved Images")
        preview = gr.Image(label="Preview Selected Image")

        list_btn.click(list_images, outputs=file_list)
        file_list.change(get_image, inputs=file_list, outputs=preview)

app = gr.mount_gradio_app(app, demo, path="/")
