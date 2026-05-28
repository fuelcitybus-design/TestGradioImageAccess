from fastapi import FastAPI

app = FastAPI()

import os
import base64
import requests
from requests.auth import HTTPBasicAuth
import gradio as gr

# --- CONFIGURATION ---
# Replace these with your actual Azure App Service credentials
APP_NAME = "oil-tank-refueling-e8a5atdqg9fnh2et"
USERNAME = "$oil-tank-refueling"
PASSWORD = "xrzqs40NcHhiqk1c2ukoTc4wTSoHHgFy77MjzRzsXlgkusz8uqhnd6KZ3tsR"
# ---------------------

def upload_image_to_kudu(image_path):
    """
    Takes the local temporary file path provided by Gradio,
    extracts the file name, and uploads it to Azure Kudu VFS.
    """
    if not image_path:
        return "⚠️ Please select or drop an image first."

    # 1. Extract the actual filename from the temporary path
    target_file_name = os.path.basename(image_path)
    
    # 2. Build the Kudu VFS URL targeting your specific directory
    # Note: Ensure 'images' directory exists, or change path to 'site/wwwroot/'
    url = f"oil-tank-refueling-e8a5atdqg9fnh2et.scm.eastasia-01.azurewebsites.net/api/vfs/site/wwwroot/{target_file_name}"
    
    headers = {
        "If-Match": "*"  # Overwrites the file if it already exists
    }

    try:
        # 3. Open the image in binary mode and send it
        with open(image_path, 'rb') as img_file:
            response = requests.put(
                url, 
                headers=headers, 
                data=img_file, 
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                timeout=30  # Prevents hanging on slow connections
            )
        
        # 4. Handle response states
        if response.status_code in [200, 201, 204]:
            return f"✅ Success! Uploaded '{target_file_name}' to Kudu file manager."
        elif response.status_code == 404:
            return f"❌ Error 404: The target directory does not exist on Kudu. Ensure 'site/wwwroot/images/' exists."
        else:
            return f"❌ Failed: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"💥 An unexpected error occurred: {str(e)}"

# --- GRADIO INTERFACE SETUP ---
with gr.Blocks(title="Kudu Image Uploader") as demo:
    gr.Markdown("# 🌐 Azure App Service Image Deployer")
    gr.Markdown("Upload an image below to programmatically send it straight to your Kudu File Manager.")
    
    with gr.Row():
        # Input component set to 'filepath' to get the local system location of the image
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
