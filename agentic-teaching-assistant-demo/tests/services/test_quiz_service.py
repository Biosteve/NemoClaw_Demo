"""
Tests for QuizService - Gradio-agnostic quiz business logic.

These tests verify that QuizService returns DTOs (not Gradio components)
and correctly handles quiz state management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from services.quiz_service import QuizService
from dto import QuizState, QuizResult, QuizQuestion


class TestQuizService:
    """Unit tests for QuizService."""
    
    @pytest.fixture
    def temp_mnt(self, tmp_path):
        """Create a temporary mnt directory."""
        mnt_dir = tmp_path / "mnt"
        mnt_dir.mkdir()
        return str(mnt_dir)
    
    @pytest.fixture
    def service(self, temp_mnt):
        """Create QuizService with temp directory."""
        return QuizService(mnt_folder=temp_mnt)
    
    @pytest.fixture
    def sample_quiz_data(self):
        """Sample quiz data for testing."""
        return [
            {
                "question": "What is 2 + 2?",
                "choices": ["(A) 3", "(B) 4", "(C) 5", "(D) 6"],
                "answer": "(B)",
                "explanation": "2 + 2 equals 4."
            },
            {
                "question": "What is the capital of France?",
                "choices": ["(A) Berlin", "(B) Madrid", "(C) Paris", "(D) Rome"],
                "answer": "(C)",
                "explanation": "Paris is the capital of France."
            },
            {
                "question": "Which planet is closest to the Sun?",
                "choices": ["(A) Venus", "(B) Mercury", "(C) Earth", "(D) Mars"],
                "answer": "(B)",
                "explanation": "Mercury is the closest planet to the Sun."
            }
        ]
    
    @pytest.fixture
    def mock_user_state(self, sample_quiz_data):
        """Mock user state with quiz data."""
        return {
            "curriculum": [{
                "active_chapter": {
                    "name": "Test Chapter",
                    "sub_topics": [{
                        "sub_topic": "Test Topic",
                        "study_material": "Test material",
                        "quizzes": sample_quiz_data
                    }]
                }
            }]
        }
    
    # =========================================================================
    # Test: Service returns DTOs, not Gradio components
    # =========================================================================
    
    def test_init_quiz_returns_quiz_state_dto(self, service, sample_quiz_data):
        """init_quiz returns QuizState dataclass, not Gradio updates."""
        # Patch the data loading to use our sample data
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.get_current_state()
        
        # Verify it's a DTO, not Gradio
        assert isinstance(state, QuizState)
        assert isinstance(state.questions, list)
        assert all(isinstance(q, QuizQuestion) for q in state.questions)
        assert isinstance(state.current_index, int)
        assert isinstance(state.progress_text, str)
        assert isinstance(state.show_prev, bool)
        assert isinstance(state.show_next, bool)
        assert isinstance(state.show_submit, bool)
    
    def test_submit_quiz_returns_quiz_result_dto(self, service, sample_quiz_data):
        """submit_quiz returns QuizResult dataclass, not Gradio updates."""
        service._quiz_data = sample_quiz_data
        service._user_answers = ["(B)", "(C)", "(B)"]  # All correct
        
        result = service.submit_quiz()
        
        # Verify it's a DTO, not Gradio
        assert isinstance(result, QuizResult)
        assert isinstance(result.score, int)
        assert isinstance(result.total, int)
        assert isinstance(result.percentage, int)
        assert isinstance(result.results_text, str)
        assert isinstance(result.question_results, list)
    
    # =========================================================================
    # Test: Quiz state management
    # =========================================================================
    
    def test_init_quiz_sets_initial_state(self, service, sample_quiz_data):
        """init_quiz sets current_index to 0 and creates empty answers."""
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.get_current_state()
        
        assert state.current_index == 0
        assert state.total == 3
        assert state.progress_text == "Question 1 of 3"
        assert state.show_prev is False  # Can't go back from first
        assert state.show_next is True   # Can go forward
        assert state.show_submit is False  # Not on last question
    
    def test_next_question_increments_index(self, service, sample_quiz_data):
        """next_question increments current_index."""
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.next_question()
        
        assert state.current_index == 1
        assert state.progress_text == "Question 2 of 3"
        assert state.show_prev is True   # Can go back now
        assert state.show_next is True   # Can still go forward
        assert state.show_submit is False
    
    def test_previous_question_decrements_index(self, service, sample_quiz_data):
        """previous_question decrements current_index."""
        service._quiz_data = sample_quiz_data
        service._current_index = 2  # Start at last question
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.previous_question()
        
        assert state.current_index == 1
        assert state.progress_text == "Question 2 of 3"
    
    def test_last_question_shows_submit(self, service, sample_quiz_data):
        """On last question, show_submit is True and show_next is False."""
        service._quiz_data = sample_quiz_data
        service._current_index = 2  # Last question (index 2 of 3)
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.get_current_state()
        
        assert state.show_next is False
        assert state.show_submit is True
    
    def test_cannot_go_before_first_question(self, service, sample_quiz_data):
        """previous_question does nothing when at first question."""
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.previous_question()
        
        assert state.current_index == 0  # Still at 0
    
    def test_cannot_go_past_last_question(self, service, sample_quiz_data):
        """next_question does nothing when at last question."""
        service._quiz_data = sample_quiz_data
        service._current_index = 2  # Last question
        service._user_answers = [None] * len(sample_quiz_data)
        
        state = service.next_question()
        
        assert state.current_index == 2  # Still at 2
    
    # =========================================================================
    # Test: Answer recording
    # =========================================================================
    
    def test_record_answer_stores_answer(self, service, sample_quiz_data):
        """record_answer stores the answer for current question."""
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        service.record_answer("(B)")
        
        assert service._user_answers[0] == "(B)"
        assert service._user_answers[1] is None  # Others unchanged
    
    def test_record_answer_for_different_questions(self, service, sample_quiz_data):
        """record_answer stores answers for multiple questions."""
        service._quiz_data = sample_quiz_data
        service._current_index = 0
        service._user_answers = [None] * len(sample_quiz_data)
        
        service.record_answer("(A)")
        service._current_index = 1
        service.record_answer("(C)")
        service._current_index = 2
        service.record_answer("(B)")
        
        assert service._user_answers == ["(A)", "(C)", "(B)"]
    
    # =========================================================================
    # Test: Quiz submission and scoring
    # =========================================================================
    
    def test_submit_quiz_all_correct(self, service, sample_quiz_data):
        """submit_quiz calculates 100% for all correct answers."""
        service._quiz_data = sample_quiz_data
        service._user_answers = ["(B)", "(C)", "(B)"]  # All correct
        
        result = service.submit_quiz()
        
        assert result.score == 3
        assert result.total == 3
        assert result.percentage == 100
        assert "3/3" in result.results_text
        assert "100%" in result.results_text
    
    def test_submit_quiz_all_wrong(self, service, sample_quiz_data):
        """submit_quiz calculates 0% for all wrong answers."""
        service._quiz_data = sample_quiz_data
        service._user_answers = ["(A)", "(A)", "(A)"]  # All wrong
        
        result = service.submit_quiz()
        
        assert result.score == 0
        assert result.total == 3
        assert result.percentage == 0
    
    def test_submit_quiz_partial_correct(self, service, sample_quiz_data):
        """submit_quiz calculates correct percentage for partial answers."""
        service._quiz_data = sample_quiz_data
        service._user_answers = ["(B)", "(A)", "(A)"]  # 1 correct, 2 wrong
        
        result = service.submit_quiz()
        
        assert result.score == 1
        assert result.total == 3
        assert result.percentage == 33  # int(1/3 * 100)
    
    def test_submit_quiz_with_no_answers(self, service, sample_quiz_data):
        """submit_quiz handles None answers (unanswered questions)."""
        service._quiz_data = sample_quiz_data
        service._user_answers = [None, None, None]
        
        result = service.submit_quiz()
        
        assert result.score == 0
        assert "No answer" in result.results_text
    
    def test_submit_quiz_question_results_structure(self, service, sample_quiz_data):
        """submit_quiz returns structured question_results."""
        service._quiz_data = sample_quiz_data
        service._user_answers = ["(B)", "(A)", "(B)"]  # 1 wrong in middle
        
        result = service.submit_quiz()
        
        assert len(result.question_results) == 3
        
        # First question - correct
        assert result.question_results[0]["is_correct"] is True
        assert result.question_results[0]["user_answer"] == "(B)"
        
        # Second question - wrong
        assert result.question_results[1]["is_correct"] is False
        assert result.question_results[1]["user_answer"] == "(A)"
        assert result.question_results[1]["explanation"] is not None
    
    # =========================================================================
    # Test: Fallback quiz
    # =========================================================================
    
    def test_fallback_quiz_when_no_data(self, service):
        """Service provides fallback quiz when no data available."""
        fallback = service._get_fallback_quiz()
        
        assert len(fallback) == 1
        assert "capital of France" in fallback[0]["question"]
        assert fallback[0]["answer"] == "(C)"
    
    # =========================================================================
    # Test: QuizState.from_quiz_data factory
    # =========================================================================
    
    def test_quiz_state_from_quiz_data(self, sample_quiz_data):
        """QuizState.from_quiz_data creates correct state."""
        user_answers = ["(B)", None, None]
        
        state = QuizState.from_quiz_data(
            quiz_data=sample_quiz_data,
            current_index=0,
            user_answers=user_answers
        )
        
        assert len(state.questions) == 3
        assert state.questions[0].user_answer == "(B)"
        assert state.questions[1].user_answer is None
        assert state.current_index == 0
        assert state.total == 3


class TestQuizServiceIntegration:
    """Integration tests that verify QuizService with mocked data layer."""
    
    @pytest.fixture
    def temp_mnt(self, tmp_path):
        """Create a temporary mnt directory."""
        mnt_dir = tmp_path / "mnt"
        mnt_dir.mkdir()
        return str(mnt_dir)
    
    @pytest.mark.asyncio
    async def test_init_quiz_loads_user_data(self, temp_mnt):
        """init_quiz loads quiz data from user state."""
        service = QuizService(mnt_folder=temp_mnt)
        
        mock_user_state = {
            "curriculum": [{
                "active_chapter": {
                    "name": "Biology 101",
                    "sub_topics": [{
                        "sub_topic": "Cells",
                        "study_material": "Cells are...",
                        "quizzes": [{
                            "question": "What is a cell?",
                            "choices": ["(A) Unit of life", "(B) A rock", "(C) A star", "(D) Water"],
                            "answer": "A",
                            "citations": ["Biology textbook p.1"],
                            "thought_process": "Cells are basic units"
                        }]
                    }]
                }
            }]
        }
        
        with patch('services.quiz_service.init_user_storage', return_value=("/path", "/userdir")):
            with patch('services.quiz_service.load_user_state', return_value=mock_user_state):
                state = service.init_quiz(username="test_user")
        
        assert isinstance(state, QuizState)
        assert state.total >= 1


