"""
Standalone Gradio App for Video Query Testing with Qwen3-Omni
Allows users to upload videos and query them using the updated vLLM client
"""
import sys
from pathlib import Path
# Add parent directory to path so we can import from root-level modules
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import gradio as gr
import os
import sys
from vllm_client_multimodal_requests import query_qwen_vllm_served

# Default system prompt for video understanding
DEFAULT_SYSTEM_PROMPT = """You are an intelligent video analysis assistant powered by Qwen3-Omni. 
You can understand and analyze video content, including visual elements, motion, actions, scenes, and context.
Provide detailed, accurate, and helpful responses based on the video content."""

def process_video_query(video_file, user_query, system_prompt, include_image, image_file, include_audio, audio_file):
    """
    Process user query with video and optional image/audio inputs
    
    Args:
        video_file: Path to uploaded video file
        user_query: User's question about the video
        system_prompt: System prompt for the model
        include_image: Whether to include an image
        image_file: Path to uploaded image file
        include_audio: Whether to include audio
        audio_file: Path to uploaded audio file
    
    Returns:
        Model response as string
    """
    
    if not video_file:
        return "❌ Please upload a video file first."
    
    if not user_query or user_query.strip() == "":
        return "❌ Please enter a question about the video."
    
    try:
        # Prepare parameters
        img_loc = image_file if include_image and image_file else None
        audio_loc = audio_file if include_audio and audio_file else None
        video_loc = video_file
        
        # Use default system prompt if none provided
        sys_prompt = system_prompt if system_prompt.strip() else DEFAULT_SYSTEM_PROMPT
        
        # Call the vLLM client
        response = query_qwen_vllm_served(
            query=user_query,
            image_file_loc=img_loc,
            sys_prompt=sys_prompt,
            audio_path=audio_loc,
            video_path=video_loc
        )
        
        return response
    
    except Exception as e:
        return f"❌ Error processing request: {str(e)}\n\nPlease ensure the vLLM server is running and accessible."


def create_ui():
    """Create and configure the Gradio interface"""
    
    with gr.Blocks(title="Video Query with Qwen3-Omni", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎬 Video Query with Qwen3-Omni
        
        Upload a video and ask questions about its content. The AI can analyze visual elements, 
        actions, scenes, motion, and context within the video.
        
        **Supported formats**: MP4, AVI, MOV, MKV, WebM
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📹 Video Input")
                video_input = gr.Video(
                    label="Upload Video",
                    format="mp4"
                )
                
                gr.Markdown("### ❓ Your Question")
                query_input = gr.Textbox(
                    label="Ask about the video",
                    placeholder="e.g., What is happening in this video? Describe the main actions and scenes.",
                    lines=3
                )
                
                gr.Markdown("### 🎯 Example Queries")
                example_queries = gr.Markdown("""
                - What is happening in this video?
                - Describe the main actions and events
                - What objects or people do you see?
                - Summarize the video content
                - What is the setting or environment?
                - Describe any text visible in the video
                """)
                
                # Optional multimodal inputs
                with gr.Accordion("🔧 Advanced Options (Optional)", open=False):
                    system_prompt_input = gr.Textbox(
                        label="Custom System Prompt",
                        placeholder="Leave empty to use default",
                        lines=3,
                        value=""
                    )
                    
                    with gr.Row():
                        include_image_check = gr.Checkbox(label="Include Image", value=False)
                        include_audio_check = gr.Checkbox(label="Include Audio", value=False)
                    
                    image_input = gr.Image(
                        label="Additional Image (Optional)",
                        type="filepath",
                        visible=False
                    )
                    
                    audio_input = gr.Audio(
                        label="Additional Audio (Optional)",
                        type="filepath",
                        visible=False
                    )
                    
                    # Toggle visibility of image/audio inputs
                    include_image_check.change(
                        fn=lambda x: gr.update(visible=x),
                        inputs=[include_image_check],
                        outputs=[image_input]
                    )
                    
                    include_audio_check.change(
                        fn=lambda x: gr.update(visible=x),
                        inputs=[include_audio_check],
                        outputs=[audio_input]
                    )
                
                submit_btn = gr.Button("🚀 Analyze Video", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### 🤖 AI Response")
                output_box = gr.Textbox(
                    label="Analysis Result",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True
                )
        
        # Example videos section
        gr.Markdown("""
        ---
        ### 💡 Tips for Best Results
        
        1. **Clear Videos**: Use videos with good lighting and clear visuals
        2. **Specific Questions**: Ask specific questions about what you want to know
        3. **Video Length**: Shorter videos (< 2 minutes) work best
        4. **Format**: MP4 format is recommended for best compatibility
        5. **Multiple Queries**: You can ask follow-up questions about the same video
        """)
        
        # Connect the submit button
        submit_btn.click(
            fn=process_video_query,
            inputs=[
                video_input,
                query_input,
                system_prompt_input,
                include_image_check,
                image_input,
                include_audio_check,
                audio_input
            ],
            outputs=[output_box]
        )
        
        # Add some example interactions
        gr.Markdown("""
        ---
        ### 📚 Example Use Cases
        
        - **Education**: Analyze educational videos, lectures, demonstrations
        - **Security**: Review surveillance footage, identify events
        - **Content Review**: Summarize video content, extract key information
        - **Accessibility**: Generate descriptions for visually impaired users
        - **Research**: Analyze experimental footage, document observations
        """)
    
    return demo


if __name__ == "__main__":
    print("🚀 Starting Video Query Gradio App...")
    print("📍 Server URL will be displayed below")
    print("⚠️  Make sure vLLM server is running at http://vllm:8901")
    print("-" * 60)
    
    # Create and launch the interface
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,        # Default Gradio port
        share=False,             # Set to True to create public link
        debug=True
    )

