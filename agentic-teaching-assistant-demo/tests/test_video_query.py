import sys
from pathlib import Path
# Add parent directory to path so we can import from root-level modules
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
"""
Test script for video query functionality
Demonstrates how to use the video processing capabilities
"""

import os
import sys
import pytest
from vllm_client_multimodal_requests import query_qwen_vllm_served

@pytest.mark.skip(reason="Manual test script - requires video_path argument")
def test_video_query(video_path, query="What is happening in this video?"):
    """
    Test video query functionality
    
    Args:
        video_path: Path to video file
        query: Question to ask about the video
    
    Returns:
        Response from the model
    """
    
    print("=" * 70)
    print("🎬 VIDEO QUERY TEST")
    print("=" * 70)
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at: {video_path}")
        print("\nPlease provide a valid video file path.")
        return None
    
    print(f"📹 Video: {video_path}")
    print(f"❓ Query: {query}")
    print("\n" + "-" * 70)
    print("🔄 Sending request to vLLM server...")
    print("-" * 70 + "\n")
    
    try:
        # Query with video
        response = query_qwen_vllm_served(
            query=query,
            image_file_loc=None,
            sys_prompt="You are an intelligent video analysis assistant. Provide detailed and accurate descriptions of video content.",
            audio_path=None,
            video_path=video_path
        )
        
        print("✅ Response received!\n")
        print("=" * 70)
        print("🤖 AI RESPONSE")
        print("=" * 70)
        print(response)
        print("=" * 70 + "\n")
        
        return response
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}\n")
        print("Possible issues:")
        print("  1. vLLM server is not running")
        print("  2. Server is not accessible at http://vllm:8901")
        print("  3. Video format is not supported")
        print("  4. Video file is too large")
        print("\nPlease check the server status and try again.")
        return None


@pytest.mark.skip(reason="Manual test script - requires video_path argument")
def test_multimodal_query(video_path, image_path=None, audio_path=None, query="Describe all the provided media"):
    """
    Test multimodal query with video, image, and audio
    
    Args:
        video_path: Path to video file
        image_path: Path to image file (optional)
        audio_path: Path to audio file (optional)
        query: Question about all media
    
    Returns:
        Response from the model
    """
    
    print("=" * 70)
    print("🎬🖼️🎵 MULTIMODAL QUERY TEST")
    print("=" * 70)
    
    # Check files
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at: {video_path}")
        return None
    
    if image_path and not os.path.exists(image_path):
        print(f"❌ Error: Image file not found at: {image_path}")
        return None
    
    if audio_path and not os.path.exists(audio_path):
        print(f"❌ Error: Audio file not found at: {audio_path}")
        return None
    
    print(f"📹 Video: {video_path}")
    if image_path:
        print(f"🖼️  Image: {image_path}")
    if audio_path:
        print(f"🎵 Audio: {audio_path}")
    print(f"❓ Query: {query}")
    print("\n" + "-" * 70)
    print("🔄 Sending multimodal request to vLLM server...")
    print("-" * 70 + "\n")
    
    try:
        response = query_qwen_vllm_served(
            query=query,
            image_file_loc=image_path,
            sys_prompt="You are an expert multimodal analyst. Analyze all provided media comprehensively.",
            audio_path=audio_path,
            video_path=video_path
        )
        
        print("✅ Response received!\n")
        print("=" * 70)
        print("🤖 AI RESPONSE")
        print("=" * 70)
        print(response)
        print("=" * 70 + "\n")
        
        return response
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}\n")
        print("Please check server status and file paths.")
        return None


def run_example_tests():
    """Run example tests if video files are available"""
    
    print("\n" + "=" * 70)
    print("🧪 VIDEO QUERY TEST SUITE")
    print("=" * 70 + "\n")
    
    print("This script tests the video query functionality.")
    print("You need to provide a video file to test.\n")
    
    # Check for test video in test_pdfs directory or current directory
    test_locations = [
        "test_videos/sample.mp4",
        "sample.mp4",
        "test.mp4",
        "video.mp4"
    ]
    
    video_found = None
    for location in test_locations:
        if os.path.exists(location):
            video_found = location
            break
    
    if video_found:
        print(f"✅ Found test video: {video_found}\n")
        
        # Run basic test
        print("📝 Test 1: Basic video query")
        test_video_query(video_found, "What is happening in this video?")
        
        print("\n📝 Test 2: Detailed description")
        test_video_query(video_found, "Provide a detailed description of all visual elements, actions, and scenes in this video.")
        
    else:
        print("❌ No test video found in standard locations.")
        print("\n📖 USAGE INSTRUCTIONS:")
        print("\nMethod 1 - Command line:")
        print('  python test_video_query.py "path/to/your/video.mp4"')
        
        print("\nMethod 2 - Python code:")
        print('  from test_video_query import test_video_query')
        print('  test_video_query("path/to/video.mp4", "What is in this video?")')
        
        print("\nMethod 3 - Use Gradio app:")
        print('  python video_query_gradio_app.py')
        print('  Then open http://localhost:7860 in your browser')
        
        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Video path provided as command line argument
        video_path = sys.argv[1]
        
        # Optional query argument
        query = sys.argv[2] if len(sys.argv) > 2 else "What is happening in this video?"
        
        # Check for additional media
        if len(sys.argv) > 4:
            # Format: python test_video_query.py video.mp4 "query" image.jpg audio.wav
            image_path = sys.argv[3] if sys.argv[3].lower() != "none" else None
            audio_path = sys.argv[4] if sys.argv[4].lower() != "none" else None
            test_multimodal_query(video_path, image_path, audio_path, query)
        else:
            test_video_query(video_path, query)
    else:
        # No arguments provided, run example tests
        run_example_tests()

