"""Hugging Face Spaces Entrypoint for Kurra Cadastral Partition System.

Mounts the production FastAPI application onto Gradio, serving both:
1. All REST API endpoints at /api/... for the Next.js frontend
2. An interactive status and diagnostic dashboard at the root URL
"""
import os
import gradio as gr
from kurra.api.main import app as fastapi_app

# Create interactive diagnostic dashboard
with gr.Blocks(title="Kurra Cadastral Partition & Demarcation Engine") as demo:
    gr.Markdown("# 🏛️ Revenue Court of Uttar Pradesh — Kurra Partition Engine")
    gr.Markdown(
        "Deterministic statutory partition, road frontage allocation, and cadastral demarcation under "
        "**UP Revenue Code, 2006 (Section 116/117 & Rule 109(5))**."
    )
    
    with gr.Row():
        gr.Markdown("### 📡 API Services Live")
    
    with gr.Row():
        gr.Markdown("""
        * **`/api/health`** — Engine & CRS status probe
        * **`/api/plots/{dist}/{teh}/{vill}/{plot}`** — Cadastral plot vector geometry & Khatauni co-sharers
        * **`/api/propose`** — Multi-variation statutory partition optimizer
        * **`/api/plans/custom-cut`** — Interactive manual pencil cut & demarcation solver
        * **`/api/media/status`** — Cloudinary CDN optimization status
        """)
        
    gr.Markdown("---")
    gr.Markdown("*Engine: FastAPI + Shapely 2.0 + OR-Tools + Cloudinary CDN*")

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
