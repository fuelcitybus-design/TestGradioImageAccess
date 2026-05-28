from fastapi import FastAPI
import gradio as gr
import os

app = FastAPI()

def save_and_return_path(image_path):
    home_dir = os.environ.get("HOME", "/home")
    save_path = os.path.join(home_dir, os.path.basename(image_path))
    with open(image_path, "rb") as src, open(save_path, "wb") as dst:
        dst.write(src.read())
    return save_path  # Gradio File output lets user download

with gr.Blocks() as demo:
    gr.Markdown("## Upload and Access Images in Azure App Service")
    img_input = gr.Image(type="filepath", label="Upload an image")
    upload_btn = gr.Button("Save to Azure Storage")
    file_output = gr.File(label="Download Saved Image")

    upload_btn.click(save_and_return_path, inputs=img_input, outputs=file_output)

app = gr.mount_gradio_app(app, demo, path="/")
