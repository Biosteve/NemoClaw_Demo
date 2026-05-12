import gradio as gr
import pandas as pd
import os, re
import random
import time
from typing import List, Tuple, Optional
from colorama import Fore
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# ============================================================================
# STUDY BUDDY APP - Sample data and functions
# ============================================================================

# Sample data for demonstration - Hierarchical structure
# Note: Maximum 10 subtopics per main topic
SAMPLE_CURRICULUM = [
    {
        "topic": "Introduction to Biology",
        "subtopics": [
            "Introduction to Biology - Cell Biology",
            "Introduction to Biology - Genetics",
            "Introduction to Biology - Ecology",
            "Introduction to Biology - Evolution",
            "Introduction to Biology - Human Anatomy"
        ]  # Max 10 subtopics allowed
    },
    "Cell Structure and Function",
    "Genetics and Heredity",
    "Evolution and Natural Selection",
    "Ecology and Ecosystems"
]

SAMPLE_QUIZ_DATA = {
    "Introduction to Biology": {
        "questions": [
            {
                "question": "What is the basic unit of life?",
                "choices": ["Atom", "Molecule", "Cell", "Organ", "Tissue"],
                "answer": "Cell",
                "explanation": "Cells are the basic structural and functional units of all living organisms."
            },
            {
                "question": "Which of these is NOT a characteristic of living things?",
                "choices": ["Reproduction", "Metabolism", "Response to stimuli", "Photosynthesis", "Growth"],
                "answer": "Photosynthesis",
                "explanation": "While photosynthesis is important for plants, not all living things perform it (e.g., animals)."
            }
        ],
        "subtopics": {
            "Introduction to Biology - Cell Biology": [
                {
                    "question": "What is the primary function of the cell membrane?",
                    "choices": ["Energy production", "Protein synthesis", "Controlling what enters and exits the cell", "Storing genetic information", "Cell division"],
                    "answer": "Controlling what enters and exits the cell",
                    "explanation": "The cell membrane is a selective barrier that regulates the passage of materials into and out of the cell."
                },
                {
                    "question": "Which structure contains the cell's genetic material?",
                    "choices": ["Cytoplasm", "Nucleus", "Mitochondria", "Cell wall", "Ribosome"],
                    "answer": "Nucleus",
                    "explanation": "The nucleus houses the cell's DNA and controls cellular activities through gene expression."
                }
            ],
            "Introduction to Biology - Genetics": [
                {
                    "question": "What molecule carries genetic information in most organisms?",
                    "choices": ["Protein", "RNA", "DNA", "Lipid", "Carbohydrate"],
                    "answer": "DNA",
                    "explanation": "DNA (deoxyribonucleic acid) stores and transmits genetic information from parents to offspring."
                },
                {
                    "question": "What are the building blocks of DNA called?",
                    "choices": ["Amino acids", "Nucleotides", "Fatty acids", "Monosaccharides", "Proteins"],
                    "answer": "Nucleotides",
                    "explanation": "DNA is made up of nucleotides, each consisting of a sugar, phosphate group, and nitrogenous base."
                }
            ],
            "Introduction to Biology - Ecology": [
                {
                    "question": "What is the term for an organism's role in its ecosystem?",
                    "choices": ["Habitat", "Niche", "Population", "Community", "Biome"],
                    "answer": "Niche",
                    "explanation": "An ecological niche describes how an organism fits into an ecosystem, including its habitat, diet, and behavior."
                },
                {
                    "question": "Which of the following represents the correct order of ecological organization from smallest to largest?",
                    "choices": ["Organism, Population, Community, Ecosystem, Biosphere", "Population, Organism, Community, Biosphere, Ecosystem", "Community, Population, Organism, Ecosystem, Biosphere", "Organism, Community, Population, Biosphere, Ecosystem", "Ecosystem, Community, Population, Organism, Biosphere"],
                    "answer": "Organism, Population, Community, Ecosystem, Biosphere",
                    "explanation": "Ecological organization progresses from individual organisms to populations (same species), communities (multiple species), ecosystems (including non-living factors), and finally the biosphere (all life on Earth)."
                }
            ],
            "Introduction to Biology - Evolution": [
                {
                    "question": "Who proposed the theory of evolution by natural selection?",
                    "choices": ["Gregor Mendel", "Louis Pasteur", "Charles Darwin", "Alfred Wallace", "Jean-Baptiste Lamarck"],
                    "answer": "Charles Darwin",
                    "explanation": "Charles Darwin published 'On the Origin of Species' in 1859, introducing the theory of evolution by natural selection."
                },
                {
                    "question": "What is a mutation?",
                    "choices": ["A change in DNA sequence", "A type of cell division", "An environmental adaptation", "A learned behavior", "A form of reproduction"],
                    "answer": "A change in DNA sequence",
                    "explanation": "Mutations are changes in the DNA sequence that can introduce new genetic variation into populations."
                }
            ],
            "Introduction to Biology - Human Anatomy": [
                {
                    "question": "What is the largest organ in the human body?",
                    "choices": ["Heart", "Liver", "Brain", "Skin", "Lungs"],
                    "answer": "Skin",
                    "explanation": "The skin is the largest organ, covering the entire body and serving as a protective barrier against pathogens and environmental damage."
                },
                {
                    "question": "Which system is responsible for transporting oxygen and nutrients throughout the body?",
                    "choices": ["Nervous system", "Digestive system", "Circulatory system", "Respiratory system", "Skeletal system"],
                    "answer": "Circulatory system",
                    "explanation": "The circulatory system, consisting of the heart, blood vessels, and blood, transports oxygen, nutrients, and other essential substances throughout the body."
                }
            ]
        }
    },
    "Cell Structure and Function": [
        {
            "question": "Which organelle is known as the 'powerhouse of the cell'?",
            "choices": ["Nucleus", "Ribosome", "Mitochondria", "Endoplasmic Reticulum", "Golgi Apparatus"],
            "answer": "Mitochondria",
            "explanation": "Mitochondria produce ATP, the cell's energy currency, through cellular respiration."
        }
    ]
}

# File upload limits
MAX_FILES = 5
MAX_FILE_SIZE_GB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024  # 1GB in bytes
MAX_PAGES_PER_FILE = 50

def validate_pdf_files(files):
    """
    Validate uploaded PDF files against size, count, and page limits.
    Returns (is_valid, error_message)
    """
    if files is None or len(files) == 0:
        return True, ""
    
    # Check number of files
    if len(files) > MAX_FILES:
        return False, f"❌ Error: You can upload a maximum of {MAX_FILES} files. You uploaded {len(files)} files."
    
    # Check each file
    for idx, file in enumerate(files):
        file_path = file.name if hasattr(file, 'name') else file
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            file_size_gb = file_size / (1024 * 1024 * 1024)
            return False, f"❌ Error: File '{os.path.basename(file_path)}' is {file_size_gb:.2f}GB. Maximum file size is {MAX_FILE_SIZE_GB}GB."
        
        
        # Check if it's a PDF
        if not file_path.lower().endswith('.pdf'):
            return False, f"❌ Error: File '{os.path.basename(file_path)}' is not a PDF file."
        
        # Check page count if PyPDF2 is available
        if PdfReader is not None:
            try:
                pdf_reader = PdfReader(file_path)
                num_pages = len(pdf_reader.pages)
                if num_pages > MAX_PAGES_PER_FILE:
                    return False, f"❌ Error: File '{os.path.basename(file_path)}' has {num_pages} pages. Maximum allowed is {MAX_PAGES_PER_FILE} pages per file."
            except Exception as e:
                return False, f"❌ Error: Unable to read PDF file '{os.path.basename(file_path)}': {str(e)}"
    
    return True, f"✅ {len(files)} file(s) uploaded successfully!"

def generate_curriculum(file_obj, validation_msg):
    """Generate curriculum from uploaded PDF or use sample data"""
    # Check if there's a validation error
    if validation_msg and validation_msg.startswith("❌"):
        # Return current state without changes if validation failed
        outputs = [gr.Column(visible=False)]
        for i in range(10):
            outputs.append(gr.Button(visible=False))
        outputs.append([])  # Empty unlocked topics
        outputs.append([])  # Empty expanded topics
        return outputs
    
    if file_obj:
        # In a real app, you would extract content from PDF here
        # For demo, we'll just return sample curriculum
        curriculum = [f"Chapter {i+1}: Extracted Topic {i+1}" for i in range(5)]
    else:
        # Flatten the hierarchical curriculum structure
        curriculum = []
        for item in SAMPLE_CURRICULUM:
            if isinstance(item, dict):
                # Add main topic
                curriculum.append(item["topic"])
                # Add subtopics with indentation (max 10 subtopics)
                subtopics_to_add = item["subtopics"][:10]  # Limit to 10 subtopics
                for subtopic in subtopics_to_add:
                    curriculum.append(f"  ↳ {subtopic}")
            else:
                # Add regular topic
                curriculum.append(item)
    
    # Initialize unlocked topics - only first subtopic under each main topic is unlocked
    unlocked_topics = set()
    for i, topic in enumerate(curriculum):
        # Main topics and non-subtopic items are always unlocked
        if not topic.startswith("  ↳ "):
            unlocked_topics.add(topic)
        # First subtopic after a main topic is unlocked
        elif i > 0 and not curriculum[i-1].startswith("  ↳ "):
            unlocked_topics.add(topic)
    
    # Create chapter buttons (10 max) - hide subtopics initially
    outputs = [gr.Column(visible=True)]
    for i in range(10):
        if i < len(curriculum):
            button_text = curriculum[i]
            is_unlocked = button_text in unlocked_topics
            is_subtopic = button_text.startswith("  ↳ ")
            # Hide subtopics initially, show main topics
            outputs.append(gr.Button(button_text, visible=not is_subtopic, interactive=is_unlocked))
        else:
            outputs.append(gr.Button(visible=False))
    
    # Return outputs + unlocked topics + expanded topics + completed topics (all empty initially)
    outputs.append(list(unlocked_topics))
    outputs.append([])  # No topics expanded initially
    outputs.append([])  # No topics completed initially
    return outputs

def handle_file_upload(files, progress=gr.Progress()):
    """Handle file upload and validate"""
    if files is None or len(files) == 0:
        return ""
    
    progress(0, desc="📤 Uploading files...")
    time.sleep(0.8)  # Make loading visible
    
    progress(0.2, desc="📋 Validating file count...")
    time.sleep(0.6)
    
    progress(0.4, desc="📏 Checking file sizes...")
    time.sleep(0.6)
    
    progress(0.6, desc="📄 Verifying PDF format...")
    time.sleep(0.6)
    
    progress(0.8, desc="🔍 Checking page counts...")
    is_valid, message = validate_pdf_files(files)
    time.sleep(0.5)
    
    progress(1.0, desc="✅ Validation complete!")
    time.sleep(0.3)
    
    return message

def toggle_subtopics(chapter_name, expanded_topics, unlocked_topics):
    """Toggle visibility of subtopics when main topic is clicked"""
    # Check if this is a main topic with subtopics
    has_subtopics = False
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict) and item["topic"] == chapter_name:
            has_subtopics = True
            break
    
    if not has_subtopics:
        # Not a main topic with subtopics, return unchanged
        curriculum = []
        for item in SAMPLE_CURRICULUM:
            if isinstance(item, dict):
                curriculum.append(item["topic"])
                for subtopic in item["subtopics"][:10]:  # Max 10 subtopics
                    curriculum.append(f"  ↳ {subtopic}")
            else:
                curriculum.append(item)
        
        button_updates = []
        for i in range(10):
            if i < len(curriculum):
                is_subtopic = curriculum[i].startswith("  ↳ ")
                is_visible = curriculum[i] in expanded_topics if is_subtopic else True
                is_unlocked = curriculum[i] in unlocked_topics
                button_updates.append(gr.Button(visible=is_visible, interactive=is_unlocked))
            else:
                button_updates.append(gr.Button(visible=False))
        
        return button_updates + [expanded_topics]
    
    # Toggle expanded state
    new_expanded = set(expanded_topics)
    if chapter_name in new_expanded:
        new_expanded.remove(chapter_name)
    else:
        new_expanded.add(chapter_name)
    
    # Flatten curriculum to get button order
    curriculum = []
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict):
            curriculum.append(item["topic"])
            for subtopic in item["subtopics"]:
                curriculum.append(f"  ↳ {subtopic}")
        else:
            curriculum.append(item)
    
    # Update button visibility
    button_updates = []
    for i in range(10):
        if i < len(curriculum):
            topic = curriculum[i]
            is_subtopic = topic.startswith("  ↳ ")
            
            if is_subtopic:
                # Find parent topic
                parent_topic = None
                for j in range(i-1, -1, -1):
                    if not curriculum[j].startswith("  ↳ "):
                        parent_topic = curriculum[j]
                        break
                # Show subtopic only if parent is expanded
                is_visible = parent_topic in new_expanded
            else:
                # Main topics are always visible
                is_visible = True
            
            is_unlocked = topic in unlocked_topics
            button_updates.append(gr.Button(visible=is_visible, interactive=is_unlocked))
        else:
            button_updates.append(gr.Button(visible=False))
    
    return button_updates + [list(new_expanded)]

def mark_chapter_complete(chapter_name, expanded_topics, unlocked_topics, completed_topics, progress=gr.Progress()):
    """Mark a chapter as complete and prepare quiz"""
    # Check if this is a main topic with subtopics
    has_subtopics = False
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict) and item["topic"] == chapter_name:
            has_subtopics = True
            break
    
    # If it's a main topic with subtopics, toggle subtopics visibility and return
    if has_subtopics:
        # Toggle expanded state
        new_expanded = set(expanded_topics)
        if chapter_name in new_expanded:
            new_expanded.remove(chapter_name)
        else:
            new_expanded.add(chapter_name)
        
        # Update button visibility but don't open quiz
        curriculum = []
        for item in SAMPLE_CURRICULUM:
            if isinstance(item, dict):
                curriculum.append(item["topic"])
                for subtopic in item["subtopics"][:10]:  # Max 10 subtopics
                    curriculum.append(f"  ↳ {subtopic}")
            else:
                curriculum.append(item)
        
        button_updates = []
        for i in range(10):
            if i < len(curriculum):
                topic = curriculum[i]
                is_subtopic = topic.startswith("  ↳ ")
                
                if is_subtopic:
                    # Find parent topic
                    parent_topic = None
                    for j in range(i-1, -1, -1):
                        if not curriculum[j].startswith("  ↳ "):
                            parent_topic = curriculum[j]
                            break
                    # Show subtopic only if parent is expanded
                    is_visible = parent_topic in new_expanded
                else:
                    # Main topics are always visible
                    is_visible = True
                
                is_unlocked = topic in unlocked_topics
                is_completed = topic in completed_topics or topic.replace("  ↳ ", "") in completed_topics
                
                # Add CSS class for completed topics
                elem_class = ["chapter-btn"]
                if is_completed:
                    elem_class.append("completed-topic")
                if is_subtopic:
                    elem_class.append("subtopic-btn")
                
                button_updates.append(gr.Button(visible=is_visible, interactive=is_unlocked, elem_classes=elem_class))
            else:
                button_updates.append(gr.Button(visible=False))
        
        # Create empty quiz components (keep quiz hidden)
        quiz_components = []
        for _ in range(10):
            quiz_components.append(gr.Radio(visible=False))
            quiz_components.append(gr.Markdown(visible=False))
        
        # Return all expected outputs (don't open quiz, just toggle subtopics)
        return (
            [gr.Accordion(visible=False),  # Keep quiz hidden
             gr.Textbox(visible=False),  # Keep score hidden
             "",  # current_chapter (empty)
             0]  # total_questions (0)
            + quiz_components  # 20 components (10 radio + 10 markdown)
            + button_updates  # 10 buttons
            + [list(new_expanded),  # expanded_topics_state
               completed_topics,  # completed_topics_state (unchanged)
               gr.Button(visible=False),  # Submit button (hidden when no quiz)
               gr.Button(visible=False)]  # Next Chapter button (hidden when no quiz)
        )
    
    progress(0.3, desc="Preparing quiz...")
    
    # Remove indentation prefix if present
    actual_chapter_name = chapter_name.replace("  ↳ ", "") if "  ↳ " in chapter_name else chapter_name
    
    # Get quiz data for the chapter - handle hierarchical structure
    quiz_data = SAMPLE_QUIZ_DATA.get(actual_chapter_name, None)
    
    # Determine if this is a main topic with subtopics, a subtopic, or a simple topic
    if isinstance(quiz_data, dict) and "questions" in quiz_data:
        # This is a main topic with subtopics, use the main topic questions
        quiz_questions = quiz_data["questions"]
    elif isinstance(quiz_data, list):
        # This is a simple topic with direct question list
        quiz_questions = quiz_data
    else:
        # Try to find it as a subtopic under its parent
        quiz_questions = []
        for topic, data in SAMPLE_QUIZ_DATA.items():
            if isinstance(data, dict) and "subtopics" in data:
                if actual_chapter_name in data["subtopics"]:
                    quiz_questions = data["subtopics"][actual_chapter_name]
                    break
    
    if not quiz_questions:
        # Generate fake questions if none exist
        quiz_questions = [
            {
                "question": f"Sample question for {chapter_name}?",
                "choices": ["Choice A", "Choice B", "Choice C", "Choice D", "Choice E"],
                "answer": "Choice A",
                "explanation": "This is a sample explanation for the question."
            }
        ]
    
    # Create quiz components (max 10 questions)
    quiz_components = []
    for i in range(10):
        if i < len(quiz_questions):
            q = quiz_questions[i]
            radio = gr.Radio(
                choices=q["choices"],
                label=f"Q{i+1}: {q['question']}",
                interactive=True,
                visible=True,
                value=None  # Reset value to None for new quiz
            )
            explanation = gr.Markdown(f"**Explanation:** {q['explanation']}", visible=False)
        else:
            radio = gr.Radio(visible=False, value=None)
            explanation = gr.Markdown(visible=False)
        quiz_components.extend([radio, explanation])
    
    total_questions = len(quiz_questions)
    counter_text = f"0/{total_questions}"
    
    # Generate button updates to maintain current state
    curriculum = []
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict):
            curriculum.append(item["topic"])
            for subtopic in item["subtopics"]:
                curriculum.append(f"  ↳ {subtopic}")
        else:
            curriculum.append(item)
    
    button_updates = []
    for i in range(10):
        if i < len(curriculum):
            topic = curriculum[i]
            is_subtopic = topic.startswith("  ↳ ")
            
            if is_subtopic:
                # Find parent topic
                parent_topic = None
                for j in range(i-1, -1, -1):
                    if not curriculum[j].startswith("  ↳ "):
                        parent_topic = curriculum[j]
                        break
                # Show subtopic only if parent is expanded
                is_visible = parent_topic in expanded_topics
            else:
                # Main topics are always visible
                is_visible = True
            
            is_unlocked = topic in unlocked_topics
            is_completed = topic in completed_topics or topic.replace("  ↳ ", "") in completed_topics
            
            # Add CSS class for completed topics
            elem_class = ["chapter-btn"]
            if is_completed:
                elem_class.append("completed-topic")
            if is_subtopic:
                elem_class.append("subtopic-btn")
            
            button_updates.append(gr.Button(visible=is_visible, interactive=is_unlocked, elem_classes=elem_class))
        else:
            button_updates.append(gr.Button(visible=False))
    
    return (
        [gr.Accordion(visible=True),
         gr.Textbox(value=counter_text, visible=True),
         actual_chapter_name,  # Current chapter name (without prefix)
         total_questions]  # Total questions
        + quiz_components
        + button_updates
        + [expanded_topics,  # Maintain expanded state
           completed_topics,  # Maintain completed state
           gr.Button(visible=True),  # Submit button (visible when quiz loads)
           gr.Button(visible=True, interactive=False)]  # Next Chapter button (visible but disabled initially)
    )

def update_button_states(unlocked_topics, expanded_topics, completed_topics):
    """Update button interactive states and visibility based on unlocked, expanded, and completed topics"""
    # Flatten curriculum to get button order
    curriculum = []
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict):
            curriculum.append(item["topic"])
            for subtopic in item["subtopics"]:
                curriculum.append(f"  ↳ {subtopic}")
        else:
            curriculum.append(item)
    
    # Create button updates (10 max)
    button_updates = []
    for i in range(10):
        if i < len(curriculum):
            topic = curriculum[i]
            is_subtopic = topic.startswith("  ↳ ")
            
            if is_subtopic:
                # Find parent topic
                parent_topic = None
                for j in range(i-1, -1, -1):
                    if not curriculum[j].startswith("  ↳ "):
                        parent_topic = curriculum[j]
                        break
                # Show subtopic only if parent is expanded
                is_visible = parent_topic in expanded_topics
            else:
                # Main topics are always visible
                is_visible = True
            
            is_unlocked = topic in unlocked_topics
            is_completed = topic in completed_topics or topic.replace("  ↳ ", "") in completed_topics
            
            # Add CSS class for completed topics
            elem_class = ["chapter-btn"]
            if is_completed:
                elem_class.append("completed-topic")
            if is_subtopic:
                elem_class.append("subtopic-btn")
            
            button_updates.append(gr.Button(visible=is_visible, interactive=is_unlocked, elem_classes=elem_class))
        else:
            button_updates.append(gr.Button())
    
    return button_updates

def check_answers(chapter_name, total_questions, unlocked_topics, expanded_topics, completed_topics, *answers):
    """Check answers and update score"""
    # Get quiz data for the chapter - handle hierarchical structure
    quiz_data = SAMPLE_QUIZ_DATA.get(chapter_name, None)
    
    # Determine if this is a main topic with subtopics, a subtopic, or a simple topic
    if isinstance(quiz_data, dict) and "questions" in quiz_data:
        # This is a main topic with subtopics, use the main topic questions
        quiz_questions = quiz_data["questions"]
    elif isinstance(quiz_data, list):
        # This is a simple topic with direct question list
        quiz_questions = quiz_data
    else:
        # Try to find it as a subtopic under its parent
        quiz_questions = []
        for topic, data in SAMPLE_QUIZ_DATA.items():
            if isinstance(data, dict) and "subtopics" in data:
                if chapter_name in data["subtopics"]:
                    quiz_questions = data["subtopics"][chapter_name]
                    break
    
    if not quiz_questions:
        quiz_questions = [
            {
                "question": f"Sample question for {chapter_name}?",
                "choices": ["Choice A", "Choice B", "Choice C", "Choice D", "Choice E"],
                "answer": "Choice A",
                "explanation": "This is a sample explanation for the question."
            }
        ]
    
    correct_count = 0
    explanations_visibility = []
    
    for i, q in enumerate(quiz_questions):
        user_answer = answers[i] if i < len(answers) else None
        correct_answer = q["answer"]
        
        if user_answer == correct_answer:
            correct_count += 1
            
        # Always show explanation after submission
        explanations_visibility.append(gr.Markdown(visible=True))
    
    # Hide remaining explanations
    for i in range(len(quiz_questions), 10):
        explanations_visibility.append(gr.Markdown(visible=False))
    
    score_text = f"{correct_count}/{total_questions}"
    
    # Check if user passed (need all questions correct to unlock next)
    passed = correct_count == total_questions
    
    # Update unlocked and completed topics if passed
    new_unlocked_topics = set(unlocked_topics)
    new_completed_topics = set(completed_topics)
    
    if passed:
        # Mark this topic as completed
        new_completed_topics.add(chapter_name)
        
        # Find the next subtopic to unlock
        curriculum = []
        for item in SAMPLE_CURRICULUM:
            if isinstance(item, dict):
                curriculum.append(item["topic"])
                for subtopic in item["subtopics"][:10]:  # Max 10 subtopics
                    curriculum.append(f"  ↳ {subtopic}")
            else:
                curriculum.append(item)
        
        # Find current topic index and unlock next if it's a subtopic
        current_full_name = f"  ↳ {chapter_name}" if not chapter_name in curriculum else chapter_name
        try:
            current_idx = curriculum.index(current_full_name)
            # Check if there's a next item and it's a subtopic in the same group
            if current_idx + 1 < len(curriculum):
                next_topic = curriculum[current_idx + 1]
                if next_topic.startswith("  ↳ "):
                    new_unlocked_topics.add(next_topic)
        except ValueError:
            pass
        
        # Check if all subtopics under a main topic are completed
        for item in SAMPLE_CURRICULUM:
            if isinstance(item, dict):
                main_topic = item["topic"]
                all_subtopics_completed = all(
                    subtopic in new_completed_topics
                    for subtopic in item["subtopics"][:10]  # Max 10 subtopics
                )
                if all_subtopics_completed:
                    new_completed_topics.add(main_topic)
    
    # Update button states (maintaining expanded and completed states)
    button_updates = update_button_states(new_unlocked_topics, expanded_topics, new_completed_topics)
    
    # Keep submit button visible, enable Next Chapter button only if passed
    submit_btn_update = gr.Button(visible=True)
    next_chapter_btn_update = gr.Button(visible=True, interactive=passed)
    
    return [gr.Textbox(value=score_text, visible=True)] + explanations_visibility + button_updates + [list(new_unlocked_topics)] + [expanded_topics] + [list(new_completed_topics)] + [submit_btn_update, next_chapter_btn_update]

def go_to_next_chapter(current_chapter, unlocked_topics, expanded_topics, completed_topics):
    """Navigate to the next unlocked chapter"""
    # Flatten curriculum to get chapter order
    curriculum = []
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict):
            curriculum.append(item["topic"])
            for subtopic in item["subtopics"]:
                curriculum.append(f"  ↳ {subtopic}")
        else:
            curriculum.append(item)
    
    # Find current chapter and get next unlocked one
    current_full_name = f"  ↳ {current_chapter}" if f"  ↳ {current_chapter}" in curriculum else current_chapter
    try:
        current_idx = curriculum.index(current_full_name)
        # Find next unlocked topic
        for i in range(current_idx + 1, len(curriculum)):
            next_topic = curriculum[i]
            if next_topic in unlocked_topics or not next_topic.startswith("  ↳ "):
                # Found next unlocked topic, open it
                return mark_chapter_complete(next_topic, expanded_topics, unlocked_topics, completed_topics)
    except (ValueError, IndexError):
        pass
    
    # If no next chapter found, return current state unchanged
    return mark_chapter_complete(current_chapter, expanded_topics, unlocked_topics, completed_topics)

def check_quiz_unlock(completed_topics):
    """Check if Quiz tab should be unlocked based on completion"""
    # Unlock Quiz tab only if a FULL topic is completed
    # A full topic is either:
    # 1. A topic without subtopics (like "Cell Structure and Function")
    # 2. A main topic whose all subtopics are completed (like "Introduction to Biology")
    
    full_topic_complete = False
    completed_set = set(completed_topics)
    
    for item in SAMPLE_CURRICULUM:
        if isinstance(item, dict):
            # This is a main topic with subtopics
            # Check if the main topic itself is in completed (meaning all subtopics done)
            if item["topic"] in completed_set:
                full_topic_complete = True
                break
        else:
            # This is a simple topic without subtopics
            if item in completed_set:
                full_topic_complete = True
                break
    
    # Return visibility updates for lock message and quiz content
    return gr.Markdown(visible=not full_topic_complete), gr.Column(visible=full_topic_complete)

def send_message(message, history, buddy_pref):
    """Handle chat messages with study buddy"""
    if not message.strip():
        return "", history
    
    # Simple response logic based on user preference
    responses = [
        f"I understand you prefer a {buddy_pref.lower() if buddy_pref else 'helpful'} study buddy!",
        "That's a great point! Let me help clarify that concept.",
        "I found some additional resources on that topic for you.",
        "Would you like me to explain that in a different way?",
        "That's an excellent question! Here's what I know about it..."
    ]
    
    bot_response = random.choice(responses)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": bot_response})
    return "", history

def submit_feedback(feedback_text):
    """Handle feedback submission"""
    if not feedback_text or not feedback_text.strip():
        return gr.Textbox(value="", visible=False), ""
    
    # In a real app, you would save this to a database or file
    # For now, we'll just show a success message
    return gr.Textbox(value="✅ Thank you for your feedback! We appreciate your input.", visible=True), ""

def clear_feedback():
    """Clear feedback form"""
    return "", gr.Textbox(value="", visible=False)

def submit_username(username):
    """Handle username submission and hide modal"""
    if not username or not username.strip():
        return (
            gr.update(visible=True),  # Keep modal visible
            gr.update(visible=False, value=""),  # Keep username display hidden
            ""  # Empty username state
        )
    
    username = username.strip()
    username_html = f'<div style="background: #f0f0f0; padding: 8px 15px; border-radius: 15px; font-weight: bold; color: #2c3e50; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: inline-block; font-size: 14px;">👤 {username}</div>'
    return (
        gr.update(visible=False),  # Hide modal
        gr.update(visible=True, value=username_html),  # Show and display username
        username  # Store username in state
    )

# ============================================================================
# CHECK QUIZ APP - CSV-based quiz functions
# ============================================================================

def load_random_csv():
    """Load a random CSV file from the directory"""
    global df
    csv_dir = 'C:\\Users\\zcharpy\\OneDrive - NVIDIA Corporation\\zeno\\DrivingLicense(SE)'
    files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not files:
        raise FileNotFoundError("No CSV files found in directory")
    f = random.choice(files)
    df = pd.read_csv(os.path.join(csv_dir, f))
    return df

# Even more robust approach:
def extract_choices_robust(choice_str):
    # First, try to separate concatenated choices
    # Look for patterns like ')''(' and insert space
    separated = re.sub(r"\)'\s*'\s*\(", ")' '(", choice_str)
    
    # Clean the string
    cleaned = re.sub(r"[\[\]'\"\\]", " ", separated)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # Extract all choices - more flexible pattern
    pattern = r"\([A-E]\)[^(\]]*?(?=\s*\([A-E]\)|\s*$)"
    matches = re.findall(pattern, cleaned)
    
    result = [match.strip() for match in matches if match.strip()]
    return result

def double_check(choice):
    print(choice)
    if '(A)' in choice and '(B)' in choice and '(C)' in choice and '(D)' in choice and '(E)' in choice:
        print("A-E")
        choices=get_choices(choice)
    elif '(A)' in choice and '(B)' in choice and '(C)' in choice and '(D)' in choice :
        print("A-D")
        choices=get_choices(choice)
    elif '(A)' in choice and '(B)' in choice and '(C)' in choice :
        print("A-C")
        choices=get_choices(choice)
    elif '(A)' in choice and '(B)' in choice:
        print("A-B")
        choices=get_choices(choice)
    elif '(A)' in choice :
        print("just A")
        choices=choice
    elif '(B)' in choice :
        print("just B")
        choices=choice
    elif '(C)' in choice :
        print("just C")
        choices=choice
    elif '(D)' in choice :
        print("just D")
        choices=choice
    elif '(E)' in choice :     
        print("just E")
        choices=choice
    else:
        print(Fore.RED+"error=\n",choice)
    return choices

# Simplest and most reliable:
def get_choices(row_nr):    
    choice_str=df.iloc[row_nr, 5]    
    choice_text = str(choice_str).replace('[','').replace(']','').replace("'","").replace('"','').strip()
    lines = [line.strip() for line in choice_text.split('\n') if line.strip()]
    
    all_choices = []
    for line in lines:
        # Handle the specific format where choices are concatenated
        # Replace ')''(' with ') ' (' to separate them properly
        fixed = re.sub(r"\)'\s*'\s*\(", ")' '(", line)
        
        # Clean up
        cleaned = ""
        for char in fixed:
            if char not in "[]":
                cleaned += char
        
        # Remove extra quotes and normalize
        cleaned = cleaned.replace("'", " ").replace("\\", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # Extract choices
        pattern = r"\([A-E]\)[^(\]]*"
        matches = re.findall(pattern, cleaned)
        
        result = [match.strip() for match in matches if match.strip()]
        #print(Fore.CYAN + "result list ", len(result), result , Fore.RESET)
        final_result = [double_check(item) for item in result]
        
        if isinstance(final_result, list):
            all_choices.extend([ch.strip() for ch in final_result if ch.strip()])
        else:
            all_choices.append(str(final_result).strip())
    if len(all_choices)<4 :
        print(Fore.RED + "extracted=", '\n', len(all_choices), all_choices , Fore.RESET)
    
    return all_choices

def get_question(row_nr):
    """
    row_nr: the index number of a pandas dataframe
    return the question as string
    """
    question=df.iloc[row_nr,3].replace('[','').replace(']','').replace("'","")
    return question

def get_answer(row_nr):
    """
    row_nr: the index number of a pandas dataframe
    return the answer as string
    """
    answer=df.iloc[row_nr,4].replace('[','').replace(']','').replace("'","")
    answer_to_index={"A":'(A)',"B": '(B)',"C":'(C)',"D":'(D)',"E":'(E)'}
    if answer in answer_to_index.keys():
        answer_idx=answer_to_index[answer]
    else:
        print(answer , "not in answer to index")
        
    return answer_idx

def get_citation_as_explain(row_nr):
    """
    row_nr: the index number of a pandas dataframe
    return the citation to the original document as the explanation of the answer 
    """
    explaination=df.iloc[row_nr,-1].replace('[','').replace(']','').replace("'","")
    return explaination

csv_dir='./sample_data'
files = [f for f in os.listdir(csv_dir) if f.endswith('.csv') and not f.startswith("summary_")]
f=random.choice(files)
df=pd.read_csv(os.path.join(csv_dir, f))
df=df.sample(n=2, replace=True)
n=len(df)
quiz_data=[]
for i in range(n):
    item={
        "question": get_question(i),
        "choices": get_choices(i),
        "answer": get_answer(i),  # Index of correct choice (0-based)
        "explanation": get_citation_as_explain(i)
    }
    quiz_data.append(item)

# Global variables to track state
current_question = 0
user_answers = []

def init_quiz():
    global current_question, user_answers
    current_question = 0
    user_answers = [None] * len(quiz_data)
    return update_question()

def update_question():
    question_data = quiz_data[current_question]
    progress = f"Question {current_question + 1} of {len(quiz_data)}"
    
    # Determine button visibility
    show_prev = current_question > 0
    show_next = current_question < len(quiz_data) - 1
    show_submit = current_question == len(quiz_data) - 1  # Show submit only on last question
    
    return (
        progress,
        question_data["question"],
        gr.update(choices=question_data["choices"], value=user_answers[current_question]),
        gr.update(visible=show_prev),
        gr.update(visible=show_next),
        gr.update(visible=show_submit)
    )

def record_answer(answer):
    print(Fore.BLUE + "recorded user answer =", answer, Fore.RESET)
    user_answers[current_question] = answer

def next_question():
    global current_question
    current_question += 1
    return update_question()

def previous_question():
    global current_question
    current_question -= 1
    return update_question()

def submit_quiz():
    correct_count = 0
    results = []
    
    for i, (question_data, user_answer) in enumerate(zip(quiz_data, user_answers)):
        #is_correct = (user_answer == question_data["answer"])
        correct_answer=question_data["answer"]
        is_correct = True  if correct_answer in user_answer else False
        if is_correct:
            correct_count += 1
            
        result_text = f"Question {i+1}: {'✅ Correct' if is_correct else '❌ Incorrect'}\n"
        result_text += f"Q: {question_data['question']}\n"
        result_text += f"Your answer: {user_answer if user_answer is not None else 'No answer'}\n"
        if not is_correct:
            # Find the correct choice text
            correct_choice_text = ""
            for choice in question_data['choices']:
                if question_data['answer'] in choice:
                    correct_choice_text = choice
                    break
            result_text += f"Correct answer: {correct_choice_text}\n"
            result_text += f"Explanation: {question_data['explanation']}\n"
        result_text += "---\n"
        results.append(result_text)
    
    score_text = f"Your score: {correct_count}/{len(quiz_data)} ({int((correct_count/len(quiz_data))*100)}%)\n\n"
    full_result = score_text + "".join(results)
    
    return (
        gr.update(visible=True),
        full_result,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False)
    )

# ============================================================================
# COMBINED UI - Two tabs
# ============================================================================

with gr.Blocks(title="Study Assistant") as demo:
    
    # Username state and components
    username_state = gr.State("")
    
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
            
            with gr.Column(scale=2):
                # Curriculum section
                curriculum_col = gr.Column(visible=False)
                with curriculum_col:
                    gr.Markdown("## Study Curriculum")
                    chapter_buttons = []
                    for i in range(10):  # Max 10 chapters
                        btn = gr.Button(visible=False, elem_classes=["chapter-btn"])
                        chapter_buttons.append(btn)
                
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
                chatbot = gr.Chatbot(height=300, type='messages')
                with gr.Row():
                    msg = gr.Textbox(
                        label="Message",
                        placeholder="Ask your study buddy anything...",
                        scale=8
                    )
                    send_btn = gr.Button("Send", scale=1)
                
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
            inputs=[file_upload],
            outputs=[validation_status]
        )
        
        generate_outputs = [curriculum_col] + chapter_buttons + [unlocked_topics_state, expanded_topics_state, completed_topics_state]
        generate_btn.click(
            generate_curriculum,
            inputs=[file_upload, validation_status],
            outputs=generate_outputs
        )
        
        # Connect chapter buttons
        mark_outputs = [
            quiz_accordion,
            score_counter,
            current_chapter,
            total_questions_state
        ] + quiz_components + chapter_buttons + [expanded_topics_state, completed_topics_state, submit_btn, next_chapter_btn]
        
        for btn in chapter_buttons:
            btn.click(
                mark_chapter_complete,
                inputs=[btn, expanded_topics_state, unlocked_topics_state, completed_topics_state],
                outputs=mark_outputs
            )
        
        # Submit answers
        submit_inputs = [current_chapter, total_questions_state, unlocked_topics_state, expanded_topics_state, completed_topics_state] + quiz_components[::2]  # Only radio components
        submit_outputs = [score_counter] + quiz_components[1::2] + chapter_buttons + [unlocked_topics_state, expanded_topics_state, completed_topics_state, submit_btn, next_chapter_btn]  # Score, explanations, button updates, states, both buttons
        submit_btn.click(
            check_answers,
            inputs=submit_inputs,
            outputs=submit_outputs
        )
        
        # Next Chapter button - opens the next unlocked chapter's quiz
        next_chapter_inputs = [current_chapter, unlocked_topics_state, expanded_topics_state, completed_topics_state]
        next_chapter_outputs = mark_outputs  # Same outputs as clicking a chapter button
        next_chapter_btn.click(
            go_to_next_chapter,
            inputs=next_chapter_inputs,
            outputs=next_chapter_outputs
        )
        
        # Chat functionality
        msg.submit(send_message, [msg, chatbot, buddy_pref], [msg, chatbot])
        send_btn.click(send_message, [msg, chatbot, buddy_pref], [msg, chatbot])
        
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
            
            demo.load(init_quiz, None, [progress, question_display, choices, prev_btn, next_btn, submit_btn_quiz])
    
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
    
    # Update Quiz tab visibility when completed_topics changes
    completed_topics_state.change(
        check_quiz_unlock,
        inputs=[completed_topics_state],
        outputs=[quiz_lock_message, quiz_content_col]
    )

# Custom CSS for better UI
demo.css = """
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

if __name__ == "__main__":
    demo.launch()

