from fastapi import FastAPI

app = FastAPI()

import gradio as gr
from ftplib import FTP_TLS
import os

# Replace with your App Service details
APP_NAME = "oil-tank-refueling-e8a5atdqg9fnh2et"  # e.g. 
USERNAME = "oil-tank-refueling\$oil-tank-refueling"
PASSWORD = "xrzqs40NcHhiqk1c2ukoTc4wTSoHHgFy77MjzRzsXlgkusz8uqhnd6KZ3tsR"

# FTPS endpoint for Azure App Service
FTPS_HOST = f"{APP_NAME}.ftp.azurewebsites.windows.net"
FTPS_DIR = "/site/wwwroot"   # or "/home" depending on storage target

def upload_image(image_path):
    file_name = os.path.basename(image_path)
    try:
        ftps = FTP_TLS(FTPS_HOST)
        ftps.login(USERNAME, PASSWORD)
        ftps.prot_p()  # secure data connection
        ftps.cwd(FTPS_DIR)

        with open(image_path, "rb") as f:
            ftps.storbinary(f"STOR {file_name}", f)

        ftps.quit()
        return f"✅ Uploaded {file_name} to {FTPS_DIR}"
    except Exception as e:
        return f"❌ Upload failed: {str(e)}"

with gr.Blocks() as demo:
    gr.Markdown("## Upload Images to Azure App Service via FTPS")

    with gr.Tab("Upload"):
        img_input = gr.Image(type="filepath", label="Select an image")
        upload_btn = gr.Button("Upload via FTPS")
        upload_output = gr.Textbox(label="Result")
        upload_btn.click(upload_image, inputs=img_input, outputs=upload_output)


app = gr.mount_gradio_app(app, demo, path="/")
