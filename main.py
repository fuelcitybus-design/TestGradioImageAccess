from fastapi import FastAPI

app = FastAPI()

from requests.auth import HTTPBasicAuth         # HTTP Basic auth for Kudu API
import gradio as gr                             # Gradio UI framework
import os                                       # Path operations (basename, path.join, makedirs, path.exists, path.splitext)
import requests 

import glob
import numpy as np

import re

# --- CONFIGURATION ---
# Replace these with your actual Azure App Service credentials
USERNAME = "$oil-tank-refueling"
PASSWORD = "E8F6BQT62Mt290N5fpK1sHAnQTnxPyvsD2vXAqmmClZnYkyYDQ1Du17aNNiK"
KUDU_HOST = "oil-tank-refueling-e8a5atdqg9fnh2et.scm.eastasia-01.azurewebsites.net"
# ---------------------

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg')

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
    url = f"https://{KUDU_HOST}/api/vfs/data/"
    
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


# === Extract image and rename it
def find_and_rename_image(current_name, new_name):
    if not current_name or not current_name.strip():
        return None, "⚠️ Please enter the current filename to search."
    if not new_name or not new_name.strip():
        return None, "⚠️ Please enter a new name for the file."
    
    old_filename = current_name.strip()
    
    # Extract original extension from the current file to prevent breaking format
    _, extension = os.path.splitext(old_filename)
    new_filename = f"{new_name.strip()}{extension}"
    
    # Define URLs for Kudu VFS operations
    old_file_url = f"https://{KUDU_HOST}/api/vfs/data/{old_filename}"
    new_file_url = f"https://{KUDU_HOST}/api/vfs/data/{new_filename}"
    
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    try:
        # STEP 1: Find the image using GET
        get_response = requests.get(old_file_url, auth=auth, timeout=20)
        
        if get_response.status_code == 404:
            return None, f"❌ File '{old_filename}' not found in data/."
        elif get_response.status_code != 200:
            return None, f"❌ Failed to fetch original file: HTTP {get_response.status_code}"
            
        # STEP 2: Upload the exact binary content under the new name using PUT
        put_headers = {"If-Match": "*"}
        put_response = requests.put(
            new_file_url, 
            headers=put_headers, 
            data=get_response.content, 
            auth=auth, 
            timeout=20
        )
        
        if put_response.status_code not in [200, 201, 204]:
            return None, f"❌ Failed to save new file: HTTP {put_response.status_code}"
            
        # STEP 3: Delete the old file name using DELETE
        delete_headers = {"If-Match": "*"}
        delete_response = requests.delete(old_file_url, headers=delete_headers, auth=auth, timeout=20)
        
        if delete_response.status_code not in [200, 204]:
            # If deletion fails, notify the user that it was copied but not renamed cleanly
            return None, f"⚠️ Copied to '{new_filename}', but failed to delete original '{old_filename}'."
            
        # STEP 4: Cache the newly named image locally to display verification to user
        temp_local_path = f"temp_renamed_{new_filename}"
        with open(temp_local_path, "wb") as f:
            f.write(get_response.content)
            
        return temp_local_path, f"✅ Success! Found '{old_filename}' and renamed it to '{new_filename}'."
        
    except Exception as e:
        return None, f"💥 Connection error during rename operation: {str(e)}"


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

    # Tab 4: Find and Rename
    with gr.Tab("Find & Rename"):
        gr.Markdown("### 🔍 Find a Server Image and Rename It")
        gr.Markdown("This fetches the file, creates a copy under the new name, and safely cleans up the old file entry.")
        
        with gr.Row():
            current_name_input = gr.Textbox(
                label="Current Filename on Server (With Extension)", 
                placeholder="e.g., photo.jpg"
            )
            new_name_input = gr.Textbox(
                label="New Name (Without Extension)", 
                placeholder="e.g., new-profile-banner"
            )
            
        with gr.Row():
            rename_btn = gr.Button("Find and Rename File", variant="primary")
            
        with gr.Row():
            # Shows the image that was successfully renamed as a visual receipt
            renamed_image_display = gr.Image(label="Renamed Image Preview", type="filepath")
            rename_status = gr.Textbox(label="Operation Logs", interactive=False)
            
        # Link the interaction pipeline
        rename_btn.click(
            fn=find_and_rename_image,
            inputs=[current_name_input, new_name_input],
            outputs=[renamed_image_display, rename_status]
        )


app = gr.mount_gradio_app(app, demo, path="/")
