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
KUDU_HOST = "oil-tank-refueling-e8a5atdqg9fnh2et.scm.eastasia-01.azurewebsites.net"
# ---------------------

def upload_image_to_kudu(image_path, custom_name):
    if not image_path:
        return "⚠️ Please select or drop an image first."

    original_name = os.path.basename(image_path)
    if custom_name and custom_name.strip():
        _, extension = os.path.splitext(original_name)
        target_file_name = f"{custom_name.strip()}{extension}"
    else:
        target_file_name = original_name
    
    url = f"https://{KUDU_HOST}/api/vfs/data/{target_file_name}"
    headers = {"If-Match": "*"}

    try:
        with open(image_path, 'rb') as img_file:
            response = requests.put(url, headers=headers, data=img_file, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=30)
        if response.status_code in [200, 201]:
            return f"✅ Success! Uploaded as '{target_file_name}' to Azure wwwroot."
        else:
            return f"❌ Failed: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"💥 Connection error: {str(e)}"

# === NEW SUBSECTION: SEARCH AND EXTRACT FOR DISPLAY ===
def fetch_and_display_image(search_filename):
    if not search_filename or not search_filename.strip():
        return None, "⚠️ Please enter a filename to search."
    
    filename = search_filename.strip()
    
    # Target the file URL directly in Kudu VFS
    url = f"https://{KUDU_HOST}/api/vfs/data/{filename}"
    
    try:
        # Request the raw binary content of the file
        response = requests.get(
            url, 
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=30
        )
        
        if response.status_code == 200:
            # Create a local temporary file to cache the image for Gradio to display
            temp_local_path = f"temp_downloaded_{filename}"
            with open(temp_local_path, "wb") as f:
                f.write(response.content)
                
            return temp_local_path, f"🔍 Found! Displaying '{filename}' from Azure."
        
        elif response.status_code == 404:
            return None, f"❌ File '{filename}' not found in data/."
        else:
            return None, f"❌ Failed to fetch: HTTP {response.status_code}"
            
    except Exception as e:
        return None, f"💥 Connection error: {str(e)}"

# === NEW SUBSECTION: FETCH ALL IMAGES FOR GALLERY VIEW ===
def load_all_stored_images():
    # Kudu returns directory structure as JSON when hitting the root path
    url = f"https://{KUDU_HOST}/api/vfs/site/wwwroot/"
    
    # We will pass a list of tuples containing (local_file_path, caption) to Gradio Gallery
    gallery_items = []
    
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=30)
        
        if response.status_code != 200:
            return [], f"❌ Failed to fetch directory contents: HTTP {response.status_code}"
        
        files_json = response.json()
        
        # Ensure directory template cleanup on restart
        if not os.path.exists("kudu_cache"):
            os.makedirs("kudu_cache")

        for item in files_json:
            # Skip items that are folders
            if item.get("mime") == "inode/directory":
                continue
                
            filename = item.get("name", "")
            
            # Filter only valid image extensions
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                # Download each image to a local workspace cache folder
                file_url = f"https://{KUDU_HOST}/api/vfs/data/{filename}"
                file_response = requests.get(file_url, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=15)
                
                if file_response.status_code == 200:
                    local_cache_path = os.path.join("kudu_cache", filename)
                    with open(local_cache_path, "wb") as f:
                        f.write(file_response.content)
                    
                    # Store path and the original filename label
                    gallery_items.append((local_cache_path, filename))
        
        if not gallery_items:
            return [], "ℹ️ Connection successful, but no images were found in site/wwwroot/."
            
        return gallery_items, f"🖼️ Loaded {len(gallery_items)} images successfully from Kudu storage."
        
    except Exception as e:
        return [], f"💥 Error accessing file structures: {str(e)}"


# --- GRADIO INTERFACE SETUP ---
with gr.Blocks(title="Azure Image Uploader") as demo:
    gr.Markdown("# 🌐 Azure App Service Image Deployer")
    gr.Markdown(f"Uploading files directly to regional host: `{KUDU_HOST}`")
    
     # Tab 1: Uploading & Renaming
    with gr.Tab("Upload Images"):
        with gr.Row():
            image_input = gr.Image(type="filepath", label="Choose or Drop Image Here")
        with gr.Row():
            name_input = gr.Textbox(label="Custom File Name (Optional)", placeholder="e.g., banner")
        with gr.Row():
            upload_btn = gr.Button("Upload to Azure", variant="primary")
        with gr.Row():
            upload_output = gr.Textbox(label="Upload Status", interactive=False)
            
        upload_btn.click(
            fn=upload_image_to_kudu,
            inputs=[image_input, name_input],
            outputs=upload_output
        )

    # Tab 2: New Search and Display System
    with gr.Tab("Search & View Files"):
        gr.Markdown("### 🔍 Fetch file from Azure storage")
        with gr.Row():
            search_input = gr.Textbox(
                label="Enter Filename with Extension", 
                placeholder="e.g., photo.jpg or banner.png"
            )
        with gr.Row():
            search_btn = gr.Button("Search Kudu Storage", variant="secondary")
        with gr.Row():
            # Outputs: An image box to display it, and a text box for status reports
            image_display = gr.Image(label="Extracted Image Result", type="filepath")
            search_status = gr.Textbox(label="Search Status", interactive=False)
            
        search_btn.click(
            fn=fetch_and_display_image,
            inputs=search_input,
            outputs=[image_display, search_status]
        )

    # Tab 3: New Gallery Viewer
    with gr.Tab("Storage Gallery"):
        gr.Markdown("### 🖼️ Remote Cloud Storage Explorer")
        load_btn = gr.Button("🔄 Refresh Cloud Gallery", variant="primary")
        gallery_status = gr.Textbox(label="System Log", value="Click refresh to view stored assets.", interactive=False)
        
        # Grid layout to display the processed images neatly
        image_gallery = gr.Gallery(
            label="All Server Images", 
            show_label=True, 
            columns=[4], 
            rows=[2], 
            object_fit="contain", 
            height="auto"
        )
        
        # Clicking the button calls the directory crawler engine
        load_btn.click(
            fn=load_all_stored_images,
            inputs=None,
            outputs=[image_gallery, gallery_status]
        )

        
app = gr.mount_gradio_app(app, demo, path="/")
