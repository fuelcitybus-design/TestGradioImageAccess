from fastapi import FastAPI

app = FastAPI()

import gradio as gr
import ftplib
import ssl
import os

def upload_to_azure_ftps(file, remote_path, ftps_host, username, password):
    """Upload a file to Azure App Service via FTPS."""
    try:
        # Connect via FTPS (FTP over SSL)
        ftps = ftplib.FTP_TLS()
        ftps.connect(ftps_host, 990)
        ftps.auth()
        ftps.prot_p()  # Enable data channel encryption
        ftps.login(username, password)
        
        # Navigate to the target directory
        remote_dir = os.path.dirname(remote_path) or "/site/wwwroot/uploads"
        try:
            ftps.cwd(remote_dir)
        except ftplib.error_perm:
            # Create directory if it doesn't exist
            ftps.mkd(remote_dir)
            ftps.cwd(remote_dir)
        
        # Upload file
        filename = os.path.basename(file.name)
        with open(file.name, "rb") as f:
            ftps.storbinary(f"STOR {filename}", f)
        
        ftps.quit()
        return f"✅ Successfully uploaded '{filename}' to {remote_dir}/{filename}"
    
    except Exception as e:
        return f"❌ Upload failed: {str(e)}"


# Gradio Interface
with gr.Blocks(title="Azure FTPS Uploader") as demo:
    gr.Markdown("# 📁 Azure App Service FTPS Image Uploader")
    gr.Markdown("Upload images to your Azure App Service Kudu storage via FTPS.")
    
    with gr.Row():
        with gr.Column():
            ftps_host = gr.Textbox(
                label="FTPS Host",
                placeholder="waws-prod-xx-xxx.ftp.azurewebsites.windows.net"
            )
            username = gr.Textbox(
                label="Username",
                placeholder="your-app-name\\$your-app-name"
            )
            password = gr.Textbox(
                label="Password",
                type="password"
            )
            remote_path = gr.Textbox(
                label="Remote Path",
                value="/site/wwwroot/uploads",
                placeholder="/site/wwwroot/uploads"
            )
            file_input = gr.File(
                label="Select Image(s)",
                file_types=["image"]
            )
            upload_btn = gr.Button("🚀 Upload", variant="primary")
        
        with gr.Column():
            output = gr.Textbox(label="Result", lines=5)
    
    upload_btn.click(
        fn=upload_to_azure_ftps,
        inputs=[file_input, remote_path, ftps_host, username, password],
        outputs=output
    )

app = gr.mount_gradio_app(app, demo, path="/")
