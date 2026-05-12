"""
Main application file combining Study Buddy and Quiz tabs.
"""
import gradio as gr
import asyncio
from config import MAX_FILES, MAX_FILE_SIZE_GB, MAX_PAGES_PER_FILE
from study_buddy_ui import (
    generate_curriculum, handle_file_upload, mark_topic_complete,
    check_answers, send_message, submit_feedback,
    clear_feedback, check_quiz_unlock, submit_username, go_to_next_chapter,
    add_user_message, stream_bot_response_simple,
    add_multimodal_user_message, stream_multimodal_bot_response
)
from study_buddy_streaming_tools import send_message_streaming
from quiz_ui import init_quiz, record_answer, next_question, previous_question, submit_quiz
from calendar_assistant import create_event_with_ai
from colorama import Fore
import os, sys, json
import yaml

def check_and_init_quiz(completed_topics, username):
    """Check if quiz should be unlocked and initialize it if so"""
    import gradio as gr
    
    # Check if quiz should be unlocked
    lock_msg_update, quiz_col_update = check_quiz_unlock(completed_topics, username)
    
    # Determine if quiz is unlocked by checking if any SUBTOPIC is completed
    # (subtopics have "↳" prefix)
    is_quiz_unlocked = False
    if completed_topics:
        for completed in completed_topics:
            if completed.strip().startswith("↳") or "  ↳" in completed:
                is_quiz_unlocked = True
                break
    
    # If quiz is now unlocked (visible), initialize it
    if is_quiz_unlocked and username:
        try:
            quiz_init_outputs = init_quiz(username)
            return (lock_msg_update, quiz_col_update) + quiz_init_outputs
        except Exception as e:
            print(Fore.RED + f"Error initializing quiz: {e}", Fore.RESET)
            # Return empty/default values if initialization fails
            return (lock_msg_update, quiz_col_update, "", "", gr.Radio(choices=[]), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
    else:
        # Quiz is still locked, return default empty values
        return (lock_msg_update, quiz_col_update, "", "", gr.Radio(choices=[]), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
import yaml

# Custom CSS
CUSTOM_CSS = """
.chapter-btn {
    margin: 5px 0;
    text-align: left;
}
.gradio-button.primary {
    background-color: #3498db;
    border: none;
}
.gradio-button.secondary {
    background-color: #2ecc71;
    border: none;
}
/* Style for subtopic buttons - smaller and lighter */
.subtopic-btn {
    font-size: 0.85em !important;
    padding: 6px 12px !important;
    margin-left: 20px !important;
}
/* Style for completed topics - green background */
.completed-topic {
    background-color: #2ecc71 !important;
    color: white !important;
    border: 2px solid #27ae60 !important;
}
.completed-topic:hover {
    background-color: #27ae60 !important;
}
/* Style for locked/disabled buttons */
button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background-color: #cccccc !important;
}

/* Make tabs more responsive/clickable */
.tab-nav button {
    padding: 12px 24px !important;
    cursor: pointer !important;
}

/* Username modal overlay */
.username-modal {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background: rgba(0, 0, 0, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 9999 !important;
}

.modal-content {
    background: white !important;
    padding: 25px 30px !important;
    border-radius: 20px !important;
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5) !important;
    width: 420px !important;
    height: 220px !important;
    max-width: 420px !important;
    max-height: 220px !important;
    text-align: center !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

.modal-content > * {
    overflow: hidden !important;
}

.modal-content h3 {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 1.3em !important;
    line-height: 1 !important;
}

.modal-content p {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.9em !important;
    line-height: 1.3 !important;
    color: #666 !important;
}

.modal-content .gradio-textbox {
    margin: 15px 0 !important;
    flex-shrink: 0 !important;
}

/* Target the outer block container */
.modal-content .block,
.modal-content .svelte-1svsvh2 {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
}

/* Target the label with border */
.modal-content .show_textbox_border,
.modal-content label.container {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
}

/* Target the input container */
.modal-content .input-container {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
}

.modal-content .gradio-textbox label > span {
    display: none !important;
}

.modal-content input[type="text"] {
    text-align: center !important;
    font-size: 1em !important;
    padding: 12px 15px !important;
    border-radius: 8px !important;
    border: 2px solid #d0d0d0 !important;
    width: 100% !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    background: white !important;
    transition: all 0.2s ease !important;
    display: block !important;
}

.modal-content input[type="text"]:focus {
    border-color: #ff6b35 !important;
    background: white !important;
    outline: none !important;
    box-shadow: 0 0 0 4px rgba(255, 107, 53, 0.12) !important;
}

.modal-content button {
    width: 100% !important;
    margin: 0 !important;
    padding: 11px !important;
    font-size: 1em !important;
    flex-shrink: 0 !important;
    border-radius: 8px !important;
}

/* Username corner display */
.username-corner {
    position: fixed !important;
    top: 15px !important;
    right: 15px !important;
    z-index: 1000 !important;
    pointer-events: none !important;
}

.username-corner > div {
    pointer-events: auto !important;
}
"""
# Use MNT_FOLDER environment variable if set, otherwise fallback to reading docker-compose.yml
global mnt_folder
mnt_folder = os.environ.get("MNT_FOLDER", None)
if not mnt_folder:
    # Fallback: try to read from docker-compose.yml (for backward compatibility)
    try:
        f = open("/workspace/docker-compose.yml", "r")
        yaml_f = yaml.safe_load(f)
        mnt_folder = yaml_f["services"]["agenticta"]["volumes"][-1].split(":")[-1]
        f.close()
    except (FileNotFoundError, KeyError, IndexError) as e:
        # Default fallback if docker-compose.yml doesn't exist or is malformed
        mnt_folder = "/workspace/mnt"
        print(Fore.YELLOW + f"Warning: Could not determine mnt_folder from docker-compose.yml, using default: {mnt_folder}", Fore.RESET)

def create_app():
    """Create and configure the Gradio application"""
    with gr.Blocks(title="Study Assistant") as demo:
        
        # Username state and components
        username_state = gr.State("")
        print(Fore.CYAN + "Initialized username_state" , username_state, Fore.RESET)
        # Username modal popup (overlay)
        username_modal = gr.Column(visible=True, elem_classes=["username-modal"])
        with username_modal:
            with gr.Column(elem_classes=["modal-content"]):
                gr.HTML('<h3 style="margin: 0; padding: 0;">Welcome</h3><p style="margin: 8px 0 0 0; padding: 0; font-size: 0.9em;">Enter a username below</p>')
                username_input = gr.Textbox(
                    label="",
                    placeholder="Username",
                    max_lines=1,
                    show_label=False
                )
                username_submit_btn = gr.Button("Start", variant="primary")
        
        # Username display (small corner box - doesn't affect layout)
        username_display = gr.HTML(
            value="",
            visible=False,
            elem_classes=["username-corner"]
        )
        
        with gr.Tab("Study Buddy"):
            gr.Markdown("# 📚 AI Study Assistant")
            
            # State variables
            current_chapter = gr.State("")
            total_questions_state = gr.State(0)
            unlocked_topics_state = gr.State([])
            expanded_topics_state = gr.State([])
            completed_topics_state = gr.State([])
            # State for calendar events created from chat
            calendar_event_state = gr.State(None)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## Upload Study Material")
                    file_upload = gr.File(
                        label="Upload PDF Files",
                        file_types=[".pdf"],
                        file_count="multiple"
                    )
                    gr.Markdown(
                        f"""
                        **Upload Requirements:**
                        - Maximum {MAX_FILES} PDF files
                        - Maximum {MAX_FILE_SIZE_GB}GB per file
                        - Maximum {MAX_PAGES_PER_FILE} pages per file
                        """
                    )
                    validation_status = gr.Textbox(
                        label="Upload Status",
                        interactive=False,
                        visible=True,
                        value=""
                    )
                    generate_btn = gr.Button("Generate Curriculum")
                    
                    gr.Markdown("## Study Preferences")
                    buddy_pref = gr.Textbox(
                        label="Preferred Study Buddy Characteristics",
                        placeholder="E.g., encouraging, knowledgeable in science..."
                    )
                    
                    # Calendar Assistant Integration
                    gr.Markdown("## 📅 Quick Calendar Event")
                    calendar_accordion = gr.Accordion("Create Calendar Event with AI", open=False)
                    with calendar_accordion:
                        gr.Markdown("""
                        **Quickly create study-related calendar events using natural language!**
                        
                        Examples: *"Study session tomorrow at 3pm for 2 hours"* or *"Exam on Friday at 9am"*
                        """)
                        
                        calendar_ai_input = gr.Textbox(
                            label="Describe Your Event",
                            placeholder="e.g., Study session for Biology next Monday at 2pm for 90 minutes",
                            lines=2
                        )
                        
                        calendar_create_btn = gr.Button("🚀 Create Event", variant="secondary", size="sm")
                        
                        calendar_status = gr.Markdown("", visible=False)
                        calendar_download = gr.File(label="📥 Download .ics File", visible=False)
                        
                        with gr.Accordion("👁️ Event Preview", open=False):
                            calendar_preview = gr.Textbox(
                                label="ICS File Content",
                                lines=8,
                                max_lines=12,
                                show_copy_button=True,
                                visible=False
                            )
                    
                    # Connect calendar event handler
                    def handle_calendar_event(ai_input):
                        file_path, status, preview = create_event_with_ai(ai_input)
                        return (
                            gr.Markdown(value=status, visible=True),
                            gr.File(value=file_path, visible=True if file_path else False),
                            gr.Textbox(value=preview, visible=True if preview else False)
                        )
                    
                    calendar_create_btn.click(
                        fn=handle_calendar_event,
                        inputs=[calendar_ai_input],
                        outputs=[calendar_status, calendar_download, calendar_preview]
                    )
                
                with gr.Column(scale=2):
                    # Curriculum section
                    curriculum_col = gr.Column(visible=False)
                    with curriculum_col:
                        gr.Markdown("## Study Curriculum")
                        chapter_buttons = []
                        chapter_checkboxes = []
                        for i in range(10):  # Max 10 chapters
                            with gr.Row():
                                checkbox = gr.Checkbox(visible=False, label="", scale=1, elem_classes=["chapter-checkbox"])
                                btn = gr.Button(visible=False, elem_classes=["chapter-btn"], scale=9)
                                chapter_checkboxes.append(checkbox)
                                chapter_buttons.append(btn)
                    
                    # Study Material section - shows current subtopic material
                    study_material_section = gr.Accordion("📚 Current Study Material", open=True, visible=False)
                    with study_material_section:
                        study_material_display = gr.Markdown(
                            value="Study material will appear here after generating curriculum.",
                            elem_classes=["study-material"]
                        )
                    
                    # Quiz section
                    quiz_accordion = gr.Accordion("Quiz", visible=False)
                    with quiz_accordion:
                        with gr.Row():
                            score_counter = gr.Textbox(
                                label="Score",
                                value="0/0",
                                interactive=False,
                                visible=False
                            )
                        
                        # Quiz questions will be dynamically added here
                        quiz_components = []
                        for _ in range(10):  # Max 10 questions
                            radio = gr.Radio(visible=False)
                            explanation = gr.Markdown(visible=False)
                            quiz_components.extend([radio, explanation])
                        
                        with gr.Row():
                            submit_btn = gr.Button("Submit Answers", visible=False, scale=1)
                            next_chapter_btn = gr.Button("Next Chapter", visible=False, interactive=False, scale=1)
                    
                    # Chat section
                    gr.Markdown("## Study Buddy Chat")
                    gr.Markdown("💡 *You can now upload images along with your questions!*")
                    
                    # Streaming query router toggle
                    with gr.Row():
                        enable_streaming_router = gr.Checkbox(
                            label="🚀 Enable Streaming Query Router (Shows tool execution steps)",
                            value=False,
                            info="See detailed query routing and tool calls in real-time"
                        )
                        show_routing_details = gr.Checkbox(
                            label="📊 Show Routing Details",
                            value=True,
                            info="Display step-by-step routing and tool execution"
                        )
                    
                    # Image preview section (shows uploaded images)
                    with gr.Accordion("📷 Uploaded Images", open=True, visible=False) as image_preview_accordion:
                        image_preview = gr.Gallery(
                            label="Your uploaded images",
                            show_label=False,
                            columns=[3],  # Responsive: 3 columns
                            rows=1,
                            height=150,  # Compact but visible
                            object_fit="contain",
                            allow_preview=True,  # Allow clicking to enlarge
                            preview=False,  # Start in grid mode
                            container=True,
                            show_share_button=False,
                            show_download_button=False
                        )
                    
                    chatbot = gr.Chatbot(height=300, type='messages')
                    msg = gr.MultimodalTextbox(
                        file_count="multiple",
                        file_types=["image"],
                        sources=["upload"],
                        interactive=True,
                        placeholder="Type a message and/or upload an image...",
                        show_label=False
                    )
                    
                    # Feedback section
                    feedback_accordion = gr.Accordion("💬 Chatbot Feedback", open=False, visible=True)
                    with feedback_accordion:
                        gr.Markdown("### Help us improve the Study Buddy!\nShare your thoughts about the chatbot's responses and suggestions.")
                        feedback_input = gr.Textbox(
                            label="Your Feedback",
                            placeholder="Tell us what you think about the chatbot's responses...",
                            lines=3,
                            max_lines=5
                        )
                        with gr.Row():
                            feedback_submit_btn = gr.Button("Submit Feedback", variant="primary", scale=1)
                            feedback_clear_btn = gr.Button("Clear", scale=1)
                        feedback_status = gr.Textbox(
                            label="Status",
                            value="",
                            interactive=False,
                            visible=False
                        )
                    
                    # Summary section
                    summary_accordion = gr.Accordion("Summary", open=False, visible=True)
                    with summary_accordion:
                        gr.Markdown("Complete a chapter quiz to see your results summary here.")
            
            # Event handling for Study Buddy tab
            # Validate files on upload
            file_upload.change(
                handle_file_upload,
                inputs=[file_upload, username_state],
                outputs=[validation_status]
            )
            
            generate_outputs = [curriculum_col] + chapter_checkboxes + chapter_buttons + [study_material_section, study_material_display, unlocked_topics_state, expanded_topics_state, completed_topics_state]
            generate_btn.click(
                generate_curriculum,
                inputs=[file_upload, validation_status, username_state, buddy_pref],
                outputs=generate_outputs
            )
            
            # Buttons are now non-clickable (interactive=False), so no click handlers needed
            
            # Connect checkboxes for marking completion
            # Outputs: checkboxes + buttons + study_material_display + quiz accordion + quiz components + states + submit button
            checkbox_outputs = (chapter_checkboxes + chapter_buttons + 
                              [study_material_display, quiz_accordion, score_counter, current_chapter, total_questions_state] +
                              quiz_components + 
                              [unlocked_topics_state, expanded_topics_state, completed_topics_state, submit_btn, next_chapter_btn])
            
            # Helper function to create checkbox handler with correct index
            def make_checkbox_handler(idx):
                def handler(checkbox_value, unlocked, expanded, completed, username, *buttons):
                    return mark_topic_complete(checkbox_value, idx, unlocked, expanded, completed, username, *buttons)
                return handler
            
            for i, checkbox in enumerate(chapter_checkboxes):
                checkbox.change(
                    make_checkbox_handler(i),
                    inputs=[checkbox, unlocked_topics_state, expanded_topics_state, completed_topics_state, username_state] + chapter_buttons,
                    outputs=checkbox_outputs
                )
            
            # Submit answers
            submit_inputs = [current_chapter, total_questions_state, unlocked_topics_state, expanded_topics_state, completed_topics_state, username_state] + quiz_components[::2]
            submit_outputs = [score_counter] + quiz_components[1::2] + chapter_checkboxes + chapter_buttons + [unlocked_topics_state, expanded_topics_state, completed_topics_state, submit_btn, next_chapter_btn]
            submit_btn.click(
                check_answers,
                inputs=submit_inputs,
                outputs=submit_outputs
            )
            
            # Next Chapter button - loads the next chapter into UI after passing quiz
            next_chapter_inputs = [unlocked_topics_state, expanded_topics_state, completed_topics_state, username_state]
            next_chapter_outputs = chapter_checkboxes + chapter_buttons + [study_material_section, study_material_display, unlocked_topics_state, expanded_topics_state, completed_topics_state, submit_btn, next_chapter_btn]
            next_chapter_btn.click(
                go_to_next_chapter,
                inputs=next_chapter_inputs,
                outputs=next_chapter_outputs
            )
            
            # Chat functionality with calendar component updates
            def send_message_with_calendar(msg_text, history, pref, user):
                """Wrapper that handles chat and calendar UI updates"""
                # Call the original send_message which now returns calendar data
                new_msg, new_history, cal_file, cal_status, cal_preview = send_message(msg_text, history, pref, user)
                
                # If calendar event was created, update sidebar components
                if cal_file and cal_status:
                    print(f"Updating calendar UI with file: {cal_file}")
                    return (
                        new_msg,
                        new_history,
                        gr.Markdown(value=cal_status, visible=True),
                        gr.File(value=cal_file, visible=True),
                        gr.Textbox(value=cal_preview if cal_preview else "", visible=True if cal_preview else False)
                    )
                
                # Default: no calendar update
                return (
                    new_msg,
                    new_history,
                    gr.Markdown(visible=False),
                    gr.File(visible=False),
                    gr.Textbox(visible=False)
                )
            
            # State to store user text for streaming router
            user_text_state = gr.State("")
            
            # Dynamic chat handler based on streaming router toggle
            def handle_chat_submission(msg_content, chat_history, username, buddy_prefs, streaming_enabled, show_details):
                """Route to appropriate chat handler based on streaming toggle"""
                # Extract text from multimodal input
                if isinstance(msg_content, dict):
                    text = msg_content.get("text", "")
                    files = msg_content.get("files", [])
                else:
                    text = msg_content
                    files = []
                
                print(Fore.BLUE + f"📝 handle_chat_submission called" + Fore.RESET)
                print(Fore.BLUE + f"   Text: '{text[:50] if text else 'EMPTY'}...'" + Fore.RESET)
                print(Fore.BLUE + f"   Files: {len(files) if files else 0}" + Fore.RESET)
                print(Fore.BLUE + f"   Streaming enabled: {streaming_enabled}" + Fore.RESET)
                
                # If multimodal (images) OR streaming router disabled, use original handler
                if files or not streaming_enabled:
                    print(Fore.YELLOW + "→ Using original multimodal handler" + Fore.RESET)
                    # Use original multimodal streaming
                    # Phase 1: Add message
                    result = add_multimodal_user_message(msg_content, chat_history, username)
                    return result + (text,)  # Add text to outputs
                else:
                    print(Fore.GREEN + "→ Preparing for streaming router" + Fore.RESET)
                    # Use new streaming query router (text-only)
                    # Just clear the input box and pass through the history
                    # The user message will be added by send_message_streaming
                    return {"text": "", "files": []}, chat_history, [], gr.Accordion(visible=False), text
            
            async def handle_bot_response_streaming(chat_history, buddy_prefs, username, streaming_enabled, show_details, user_text):
                """Handle bot response with streaming router or fallback to original"""
                print(Fore.MAGENTA + f"🔄 handle_bot_response_streaming called" + Fore.RESET)
                print(Fore.MAGENTA + f"   Streaming enabled: {streaming_enabled}" + Fore.RESET)
                print(Fore.MAGENTA + f"   User text: '{user_text[:50] if user_text else 'EMPTY'}...'" + Fore.RESET)
                print(Fore.MAGENTA + f"   Chat history length: {len(chat_history) if chat_history else 0}" + Fore.RESET)
                
                # Check if we should use streaming router
                if not streaming_enabled:
                    print(Fore.YELLOW + "→ Using original handler (streaming disabled)" + Fore.RESET)
                    # Use original multimodal streaming
                    for update in stream_multimodal_bot_response(chat_history, buddy_prefs, username):
                        yield update
                        await asyncio.sleep(0)  # Give event loop time to update UI
                    return
                
                # Check if last message has images (for multimodal fallback)
                if chat_history:
                    last_msg = chat_history[-1]
                    has_images = isinstance(last_msg.get("content"), str) and "<<IMAGE_PATH:" in last_msg.get("content", "")
                    
                    if has_images:
                        print(Fore.YELLOW + "→ Using original handler (has images)" + Fore.RESET)
                        # Use original multimodal streaming for image messages
                        for update in stream_multimodal_bot_response(chat_history, buddy_prefs, username):
                            yield update
                            await asyncio.sleep(0)  # Give event loop time to update UI
                        return
                
                # Use new streaming query router with the user's text
                print(Fore.GREEN + "→ Using streaming query router" + Fore.RESET)
                # Pass the existing chat_history (without the new user message, which will be added by send_message_streaming)
                async for hist, cal_file, cal_status, cal_preview in send_message_streaming(
                    user_text,  # The text extracted from msg_content
                    chat_history,  # Existing history
                    buddy_prefs,
                    username,
                    show_details
                ):
                    yield hist
            
            # Multimodal streaming chat: split into two phases
            # Phase 1: Add user message (text + images) immediately (no queue)
            msg.submit(
                handle_chat_submission,
                [msg, chatbot, username_state, buddy_pref, enable_streaming_router, show_routing_details],
                [msg, chatbot, image_preview, image_preview_accordion, user_text_state],
                queue=False
            ).then(
                handle_bot_response_streaming,
                [chatbot, buddy_pref, username_state, enable_streaming_router, show_routing_details, user_text_state],
                [chatbot]
            )
            
            # Feedback functionality
            feedback_submit_btn.click(
                submit_feedback,
                inputs=[feedback_input],
                outputs=[feedback_status, feedback_input]
            )
            feedback_clear_btn.click(
                clear_feedback,
                inputs=[],
                outputs=[feedback_input, feedback_status]
            )
        
        with gr.Tab("Quiz"):
            gr.Markdown("# Quiz Application")
            
            # Lock message (shown when no full topics completed)
            quiz_lock_message = gr.Markdown(
                """
                ## 🔒 Quiz Tab Locked
                
                Complete a **full topic** in the Study Buddy tab to unlock this quiz section!
                
                **How to unlock:**
                - ✅ Complete a topic without subtopics (like "Cell Structure and Function"), OR
                - ✅ Complete ALL subtopics under a main topic (like all 5 subtopics under "Introduction to Biology")
                - Each question requires 100% score to proceed
                - Once a full topic is completed, this tab will unlock automatically
                """,
                visible=True
            )
            
            # Quiz content (hidden when locked)
            quiz_content_col = gr.Column(visible=False)
            with quiz_content_col:
                # State tracking
                progress = gr.Textbox(label="Progress", interactive=False)
                question_display = gr.Textbox(label="Question", interactive=False)
                choices = gr.Radio(choices=[], label="Choices", interactive=True)
                choices.change(record_answer, inputs=choices, outputs=[])
                
                with gr.Row():
                    prev_btn = gr.Button("Previous", visible=False)
                    next_btn = gr.Button("Next", visible=False)
                    submit_btn_quiz = gr.Button("Submit Quiz", visible=False)
                
                result_display = gr.Textbox(label="Results", interactive=False, visible=False)
                
                # Event handlers for Quiz tab
                next_btn.click(next_question, None, [progress, question_display, choices, prev_btn, next_btn, submit_btn_quiz])
                prev_btn.click(previous_question, None, [progress, question_display, choices, prev_btn, next_btn, submit_btn_quiz])
                submit_btn_quiz.click(submit_quiz, None, [result_display, result_display, progress, question_display, choices, submit_btn_quiz])
                
                # Initialize quiz when user accesses the quiz tab (after curriculum is generated)
                # Removed demo.load to avoid initialization errors for first-time users
        
        with gr.Tab("📅 Calendar Assistant"):
            gr.Markdown("""
            # 📅 AI Calendar Assistant
            
            Create calendar events using natural language! Describe your event and let AI parse the details.
            Download the generated `.ics` file to add to your calendar app.
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("""
                    ### Use natural language to create events
                    
                    Describe your event in plain English and let AI parse the details!
                    
                    **Examples:**
                    - "Schedule a team meeting tomorrow at 2pm for 2 hours"
                    - "Create a dentist appointment on December 5th at 10:30am"
                    - "Add project deadline next Friday at 5pm"
                    
                    **Note:** Using API key from environment variable `NVIDIA_API_KEY`
                    """)
                    
                    ai_input = gr.Textbox(
                        label="📝 Describe Your Event",
                        placeholder="e.g., Schedule a study session next Tuesday at 3pm for 90 minutes",
                        lines=4
                    )
                    
                    ai_examples = gr.Examples(
                        examples=[
                            ["Schedule a study session tomorrow at 9am for 2 hours"],
                            ["Create a homework deadline on December 15th at 11:59pm"],
                            ["Add exam preparation on Monday at 3pm for 3 hours"],
                            ["Book lab session for next Wednesday 2-4pm"],
                        ],
                        inputs=ai_input
                    )
                    
                    ai_create_btn = gr.Button("🚀 Create Event with AI", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    ai_status = gr.Markdown("ℹ️ Enter your event description above")
                    ai_download = gr.File(label="📥 Download .ics File", visible=True)
                    
                    with gr.Accordion("👁️ ICS Preview", open=False):
                        ai_preview = gr.Textbox(
                            label="ICS File Content",
                            lines=15,
                            max_lines=20,
                            show_copy_button=True
                        )
            
            # Connect AI assistant
            ai_create_btn.click(
                fn=create_event_with_ai,
                inputs=[ai_input],
                outputs=[ai_download, ai_status, ai_preview]
            )
            
            # Help section
            gr.Markdown("""
            ---
            
            ## 📥 How to Import to Your Calendar
            
            ### 🎯 EASIEST METHOD - Just Double-Click!
            
            After downloading the `.ics` file:
            1. Go to your **Downloads** folder
            2. Find the `.ics` file (named like `event_Study_Session_20241128_123456.ics`)
            3. **Double-click** the file
            4. Your default calendar app (Outlook, Calendar) will open automatically
            5. Click **Save** or **Add to Calendar** in the prompt
            
            **That's it!** The event is now in your calendar.
            
            ---
            
            ### Alternative Methods
            
            **Google Calendar:**
            1. Open [Google Calendar](https://calendar.google.com/)
            2. Click the **gear icon** → **Settings**
            3. Select **Import & Export** from the left menu
            4. Click **Select file from your computer**
            5. Choose your downloaded .ics file and click **Import**
            
            **Microsoft Outlook:**
            1. Open Outlook → **File** → **Open & Export** → **Import/Export**
            2. Select **Import an iCalendar (.ics) or vCalendar file**
            3. Browse to your .ics file and click **OK**
            
            **Apple Calendar (macOS):**
            1. Open Calendar app → **File** → **Import**
            2. Select your .ics file and choose which calendar to add it to
            
            ---
            
            💡 **Tip:** You can create multiple events - just download each .ics file separately and import them all!
            """)
        
        # Username submission event handler
        username_submit_btn.click(
            submit_username,
            inputs=[username_input],
            outputs=[username_modal, username_display, username_state]
        )
        
        # Allow Enter key to submit username
        username_input.submit(
            submit_username,
            inputs=[username_input],
            outputs=[username_modal, username_display, username_state]
        )
        
        # Update Quiz tab visibility when completed_topics changes and initialize quiz if unlocked
        completed_topics_state.change(
            check_and_init_quiz,
            inputs=[completed_topics_state, username_state],
            outputs=[quiz_lock_message, quiz_content_col, progress, question_display, choices, prev_btn, next_btn, submit_btn_quiz]
        )
    
    demo.css = CUSTOM_CSS
    return demo


if __name__ == "__main__":
    # launch.json {
    #    "name": "Python: Remote Attach",
    #    "type": "debugpy",
    #    "request": "attach",
    #    "connect": { "host": "localhost", "port": 29876 },
    #    "pathMappings": [ { "localRoot": "/local/mnt/workspace", "remoteRoot": "/local/mnt/workspace" } ],
    #    "justMyCode": false
    #},
    import os, debugpy
    if os.environ.get('D','0') == '1':
        print('Waiting for client to attach...')
        debugpy.listen(('0.0.0.0', 29876))
        debugpy.wait_for_client()
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",  # Allow access from outside the container
        server_port=7860,
        share=False,
        show_error=True
    )

