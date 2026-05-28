from fastapi import FastAPI
import gradio as gr
import os

app = FastAPI()

HOME_DIR = os.environ.get("HOME", "/home")

def save_image(image_path):
    save_path = os.path.join(HOME_DIR, os.path.basename(image_path))
    with open(image_path, "rb") as src, open(save_path, "wb") as dst:
        dst.write(src.read())
    return f"✅ Saved to {save_path}"

def list_images():
    files = [f for f in os.listdir(HOME_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return files

def get_image(file_name):
    return os.path.join(HOME_DIR, file_name)

with gr.Blocks() as demo:
    gr.Markdown("## Azure App Service Storage: Upload & Browse Images")

    with gr.Tab("Upload"):
        img_input = gr.Image(type="filepath", label="Select an image")
        upload_btn = gr.Button("Save to Azure Storage")
        upload_output = gr.Textbox(label="Result")
        upload_btn.click(save_image, inputs=img_input, outputs=upload_output)

    with gr.Tab("Browse"):
        list_btn = gr.Button("List Saved Images")
        file_list = gr.Dropdown(label="Saved Images")
        preview = gr.Image(label="Preview Selected Image")
        
        list_btn.click(list_images, outputs=file_list)
        file_list.change(get_image, inputs=file_list, outputs=preview)

app = gr.mount_gradio_app(app, demo, path="/")
