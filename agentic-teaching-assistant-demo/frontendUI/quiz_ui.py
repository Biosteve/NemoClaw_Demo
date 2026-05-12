"""
Quiz tab UI components and Gradio handlers.

This module provides Gradio-specific handlers that convert
QuizService results to Gradio component updates.

The business logic is in services/quiz_service.py.
"""
import sys
from pathlib import Path
import os
import yaml

# Add parent directory to path so we can import from root-level modules
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import gradio as gr
from colorama import Fore

from services.quiz_service import QuizService
from dto import QuizState, QuizResult

# Get mnt_folder from environment or docker-compose.yml
mnt_folder = os.environ.get("MNT_FOLDER", None)
if not mnt_folder:
    try:
        f = open("/workspace/docker-compose.yml", "r")
        yaml_f = yaml.safe_load(f)
        mnt_folder = yaml_f["services"]["agenticta"]["volumes"][-1].split(":")[-1]
        f.close()
    except (FileNotFoundError, KeyError, IndexError) as e:
        mnt_folder = "/workspace/mnt"
        print(Fore.YELLOW + f"Warning: Could not determine mnt_folder, using default: {mnt_folder}" + Fore.RESET)

# Global service instance
_quiz_service: QuizService = None


def _get_service() -> QuizService:
    """Get or create the QuizService singleton."""
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService(mnt_folder=mnt_folder)
    return _quiz_service


def _quiz_state_to_gradio(state: QuizState) -> tuple:
    """
    Convert QuizState DTO to Gradio component updates.
    
    Args:
        state: QuizState dataclass from QuizService
        
    Returns:
        Tuple of Gradio updates for:
        (progress, question, choices, prev_btn, next_btn, submit_btn)
    """
    current_question = state.questions[state.current_index]
    
    return (
        state.progress_text,
        current_question.question,
        gr.update(choices=current_question.choices, value=current_question.user_answer),
        gr.update(visible=state.show_prev),
        gr.update(visible=state.show_next),
        gr.update(visible=state.show_submit)
    )


def _quiz_result_to_gradio(result: QuizResult) -> tuple:
    """
    Convert QuizResult DTO to Gradio component updates.
    
    Args:
        result: QuizResult dataclass from QuizService
        
    Returns:
        Tuple of Gradio updates for:
        (result_visible, result_text, progress_visible, question_visible, choices_visible, submit_visible)
    """
    return (
        gr.update(visible=True),   # result_display visible
        result.results_text,        # result text content
        gr.update(visible=False),   # progress hidden
        gr.update(visible=False),   # question hidden
        gr.update(visible=False),   # choices hidden
        gr.update(visible=False)    # submit hidden
    )


# =============================================================================
# Gradio Event Handlers (thin wrappers around QuizService)
# =============================================================================

def init_quiz(username: str) -> tuple:
    """
    Initialize quiz state - Gradio handler.
    
    Args:
        username: The username to initialize quiz for
        
    Returns:
        Gradio component updates
    """
    service = _get_service()
    state = service.init_quiz(username)
    return _quiz_state_to_gradio(state)


def record_answer(answer: str) -> None:
    """
    Record user's answer - Gradio handler.
    
    Args:
        answer: The user's selected answer
    """
    service = _get_service()
    service.record_answer(answer)


def next_question() -> tuple:
    """
    Move to next question - Gradio handler.
    
    Returns:
        Gradio component updates
    """
    service = _get_service()
    state = service.next_question()
    return _quiz_state_to_gradio(state)


def previous_question() -> tuple:
    """
    Move to previous question - Gradio handler.
    
    Returns:
        Gradio component updates
    """
    service = _get_service()
    state = service.previous_question()
    return _quiz_state_to_gradio(state)


def submit_quiz() -> tuple:
    """
    Submit quiz and calculate results - Gradio handler.
    
    Returns:
        Gradio component updates
    """
    service = _get_service()
    result = service.submit_quiz()
    return _quiz_result_to_gradio(result)


# =============================================================================
# Legacy compatibility - expose internal state for existing code
# =============================================================================

def load_quiz_data(mnt_folder=mnt_folder, username=None, save_to=None):
    """
    Legacy function for backward compatibility.
    Prefer using QuizService directly.
    """
    service = _get_service()
    service._quiz_data = service._load_quiz_data(username)


def update_question():
    """
    Legacy function for backward compatibility.
    Prefer using QuizService.get_current_state() directly.
    """
    service = _get_service()
    state = service.get_current_state()
    return _quiz_state_to_gradio(state)


# Legacy global variables - for backward compatibility with existing imports
# These are deprecated; use QuizService properties instead
current_question = 0
user_answers = []
quiz_data = []
df = None
