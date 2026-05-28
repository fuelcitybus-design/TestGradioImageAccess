from fastapi import FastAPI
import gradio as gr
import os
import shutil
from datetime import datetime

app = FastAPI()

# Use /tmp directory which is always writable in Azure App Service
STORAGE_DIR = "/tmp/app_storage"

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_DIR, exist_ok=True)

def save_image(image_path):
    try:
        if image_path is None:
            return "❌ No image selected"
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = os.path.basename(image_path)
        name, ext = os.path.splitext(original_name)
        new_filename = f"{name}_{timestamp}{ext}"
        
        save_path = os.path.join(STORAGE_DIR, new_filename)
        
        # Copy the file (don't move, as Gradio deletes the temp file)
        shutil.copy(image_path, save_path)
        
        return f"✅ Saved to {new_filename}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def list_images():
    try:
        files = [f for f in os.listdir(STORAGE_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))]
        return files if files else ["No images found"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def get_image(file_name):
    if file_name and file_name != "No images found":
        return os.path.join(STORAGE_DIR, file_name)
    return None

with gr.Blocks() as demo:
    gr.Markdown("## Azure App Service Storage: Upload & Browse Images")

    with gr.Tab("Upload"):
        img_input = gr.Image(type="filepath", label="Select an image")
        upload_btn = gr.Button("Save to Azure Storage")
        upload_output = gr.Textbox(label="Result")
        upload_btn.click(save_image, inputs=img_input, outputs=upload_output)

    with gr.Tab("Browse"):
        list_btn = gr.Button("List Saved Images")
        file_list = gr.Dropdown(label="Saved Images", choices=[])
        preview = gr.Image(label="Preview Selected Image")
        
        list_btn.click(list_images, outputs=file_list)
        file_list.change(get_image, inputs=file_list, outputs=preview)

app = gr.mount_gradio_app(app, demo, path="/")
