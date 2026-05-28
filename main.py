from fastapi import FastAPI
import gradio as gr
import requests
from requests.auth import HTTPBasicAuth
import os

app = FastAPI()

# Replace with your App Service details
APP_NAME = "oil-tank-refueling"
USERNAME = "enginfo@citybus.com.hk"
PASSWORD = "ESTS2026!"

BASE_URL = f"https://oil-tank-refueling.scm.azurewebsites.net/api/vfs/home/"

auth = HTTPBasicAuth(USERNAME, PASSWORD)

def upload_to_kudu(image_path):
    file_name = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        r = requests.put(BASE_URL + file_name, data=f, auth=auth)
    return f"Upload status: {r.status_code}"

def list_images():
    r = requests.get(BASE_URL, auth=auth)
    if r.status_code == 200:
        files = [f["name"] for f in r.json() if f["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
        return files
    return []

def get_image(file_name):
    r = requests.get(BASE_URL + file_name, auth=auth)
    if r.status_code == 200:
        temp_path = f"/tmp/{file_name}"
        with open(temp_path, "wb") as f:
            f.write(r.content)
        return temp_path
    return None

with gr.Blocks() as demo:
    gr.Markdown("## Manage Azure App Service Images via Kudu API")

    with gr.Tab("Upload"):
        img_input = gr.Image(type="filepath", label="Select an image")
        upload_btn = gr.Button("Upload to Azure Storage (/home)")
        upload_output = gr.Textbox(label="Result")
        upload_btn.click(upload_to_kudu, inputs=img_input, outputs=upload_output)

    with gr.Tab("Browse"):
        list_btn = gr.Button("List Saved Images")
        file_list = gr.Dropdown(label="Saved Images")
        preview = gr.Image(label="Preview Selected Image")

        list_btn.click(list_images, outputs=file_list)
        file_list.change(get_image, inputs=file_list, outputs=preview)


app = gr.mount_gradio_app(app, demo, path="/")
