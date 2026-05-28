from fastapi import FastAPI

app = FastAPI()

import os
import base64
import requests
from requests.auth import HTTPBasicAuth
import gradio as gr

# --- CONFIGURATION ---
# Replace these with your actual Azure App Service credentials
USERNAME = "$oil-tank-refueling"
PASSWORD = "xrzqs40NcHhiqk1c2ukoTc4wTSoHHgFy77MjzRzsXlgkusz8uqhnd6KZ3tsR"
# ---------------------

# Your exact regional Kudu domain name
KUDU_HOST = "oil-tank-refueling-e8a5atdqg9fnh2et.scm.eastasia-01.azurewebsites.net"
# ---------------------

def upload_image_to_kudu(image_path):
    if not image_path:
        return "⚠️ Please select or drop an image first."

    # 1. Extract the actual filename from the temporary local path
    target_file_name = os.path.basename(image_path)
    
    # 2. Build the correct VFS URL using your explicit regional host
    # This sends the file straight to 'site/wwwroot/'
    url = f"https://{KUDU_HOST}/api/vfs/site/wwwroot/{target_file_name}"
    
    headers = {
        "If-Match": "*"  # Overwrites the file if it already exists
    }

    try:
        # 3. Open the image file in binary mode and upload it
        with open(image_path, 'rb') as img_file:
            response = requests.put(
                url, 
                headers=headers, 
                data=img_file, 
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30
            )
        
        # 4. Handle response states
        if response.status_code in [200, 201, 204]:
            return f"✅ Success! Uploaded '{target_file_name}' to Azure wwwroot."
        else:
            return f"❌ Failed: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"💥 Connection error: {str(e)}"

# --- GRADIO INTERFACE SETUP ---
with gr.Blocks(title="Azure Image Uploader") as demo:
    gr.Markdown("# 🌐 Azure App Service Image Deployer")
    gr.Markdown(f"Uploading files directly to regional host: `{KUDU_HOST}`")
    
    with gr.Row():
        image_input = gr.Image(type="filepath", label="Choose or Drop Image Here")
        
    with gr.Row():
        submit_btn = gr.Button("Upload to Azure", variant="primary")
        
    with gr.Row():
        output_text = gr.Textbox(label="Upload Status", interactive=False)

    # Link button click to the upload function
    submit_btn.click(
        fn=upload_image_to_kudu,
        inputs=image_input,
        outputs=output_text
    )

app = gr.mount_gradio_app(app, demo, path="/")
