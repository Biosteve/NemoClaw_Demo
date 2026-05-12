"""
Tests for CurriculumService.

These tests verify the Gradio-agnostic curriculum business logic.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from services.curriculum_service import CurriculumService, StudyMaterialInfo, TopicCompletionResult


class TestCurriculumServiceInit:
    """Tests for CurriculumService initialization."""
    
    def test_init_with_mnt_folder(self):
        """Test service initialization with mnt_folder."""
        service = CurriculumService(mnt_folder="/test/path")
        assert service.mnt_folder == "/test/path"


class TestFlattenCurriculum:
    """Tests for flatten_curriculum method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    def test_flatten_simple_topics(self, service):
        """Test flattening curriculum with simple topics only."""
        curriculum = ["1:Chapter 1", "2:Chapter 2", "3:Chapter 3"]
        result = service.flatten_curriculum(curriculum)
        
        assert result == ["1:Chapter 1", "2:Chapter 2", "3:Chapter 3"]
    
    def test_flatten_topics_with_subtopics(self, service):
        """Test flattening curriculum with subtopics."""
        curriculum = [
            {"topic": "1:Introduction", "subtopics": ["Overview", "Basics"]},
            "2:Advanced Topics"
        ]
        result = service.flatten_curriculum(curriculum)
        
        assert result == [
            "1:Introduction",
            "  ↳ Overview",
            "  ↳ Basics",
            "2:Advanced Topics"
        ]
    
    def test_flatten_empty_curriculum(self, service):
        """Test flattening empty curriculum."""
        result = service.flatten_curriculum([])
        assert result == []
    
    def test_flatten_mixed_curriculum(self, service):
        """Test flattening curriculum with mixed types."""
        curriculum = [
            "1:Simple Topic",
            {"topic": "2:Topic with Subs", "subtopics": ["Sub A", "Sub B", "Sub C"]},
            "3:Another Simple",
            {"topic": "4:More Subs", "subtopics": ["Sub X"]}
        ]
        result = service.flatten_curriculum(curriculum)
        
        assert len(result) == 8  # 2 simple + 1 topic + 3 subs + 1 simple + 1 topic + 1 sub
        assert result[0] == "1:Simple Topic"
        assert result[1] == "2:Topic with Subs"
        assert result[2] == "  ↳ Sub A"
        assert result[5] == "3:Another Simple"


class TestGetTopicStatus:
    """Tests for get_topic_status method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    def test_get_topic_status_all_locked(self, service):
        """Test status when all topics locked."""
        curriculum = ["1:Chapter 1", "2:Chapter 2"]
        result = service.get_topic_status(
            curriculum,
            unlocked_topics=set(),
            completed_topics=set()
        )
        
        assert len(result) == 2
        # When unlocked_topics is empty, all are considered unlocked
        assert all(t["is_unlocked"] for t in result)
        assert all(not t["is_completed"] for t in result)
    
    def test_get_topic_status_some_completed(self, service):
        """Test status with some completed topics."""
        curriculum = [
            {"topic": "1:Intro", "subtopics": ["Basics", "Advanced"]}
        ]
        completed = {"1:Intro", "  ↳ Basics"}
        
        result = service.get_topic_status(
            curriculum,
            unlocked_topics=set(),
            completed_topics=completed
        )
        
        assert len(result) == 3
        assert result[0]["is_completed"] == True  # 1:Intro
        assert result[1]["is_completed"] == True  # ↳ Basics
        assert result[2]["is_completed"] == False  # ↳ Advanced
    
    def test_get_topic_status_identifies_subtopics(self, service):
        """Test that subtopics are correctly identified."""
        curriculum = [
            {"topic": "1:Main", "subtopics": ["Sub1", "Sub2"]}
        ]
        
        result = service.get_topic_status(curriculum, set(), set())
        
        assert result[0]["is_subtopic"] == False  # Main topic
        assert result[1]["is_subtopic"] == True   # Sub1
        assert result[2]["is_subtopic"] == True   # Sub2


class TestFindNextIncompleteTopic:
    """Tests for find_next_incomplete_topic method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    def test_find_first_when_none_completed(self, service):
        """Test finding first topic when none completed."""
        curriculum = ["1:Chapter 1", "2:Chapter 2"]
        result = service.find_next_incomplete_topic(curriculum, set())
        
        assert result == "1:Chapter 1"
    
    def test_find_next_after_some_completed(self, service):
        """Test finding next after some completed."""
        curriculum = ["1:Chapter 1", "2:Chapter 2", "3:Chapter 3"]
        completed = {"1:Chapter 1", "2:Chapter 2"}
        
        result = service.find_next_incomplete_topic(curriculum, completed)
        assert result == "3:Chapter 3"
    
    def test_returns_none_when_all_completed(self, service):
        """Test returns None when all topics completed."""
        curriculum = ["1:Chapter 1", "2:Chapter 2"]
        completed = {"1:Chapter 1", "2:Chapter 2"}
        
        result = service.find_next_incomplete_topic(curriculum, completed)
        assert result is None
    
    def test_find_incomplete_subtopic(self, service):
        """Test finding incomplete subtopic."""
        curriculum = [
            {"topic": "1:Intro", "subtopics": ["Sub1", "Sub2"]}
        ]
        completed = {"1:Intro", "  ↳ Sub1"}
        
        result = service.find_next_incomplete_topic(curriculum, completed)
        assert result == "  ↳ Sub2"


class TestCalculateProgress:
    """Tests for calculate_progress method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    def test_zero_progress(self, service):
        """Test progress with nothing completed."""
        curriculum = ["1:Ch1", "2:Ch2", "3:Ch3", "4:Ch4"]
        completed, total, pct = service.calculate_progress(curriculum, set())
        
        assert completed == 0
        assert total == 4
        assert pct == 0.0
    
    def test_partial_progress(self, service):
        """Test partial progress."""
        curriculum = ["1:Ch1", "2:Ch2", "3:Ch3", "4:Ch4"]
        completed_set = {"1:Ch1", "2:Ch2"}
        
        completed, total, pct = service.calculate_progress(curriculum, completed_set)
        
        assert completed == 2
        assert total == 4
        assert pct == 50.0
    
    def test_full_progress(self, service):
        """Test 100% progress."""
        curriculum = ["1:Ch1", "2:Ch2"]
        completed_set = {"1:Ch1", "2:Ch2"}
        
        completed, total, pct = service.calculate_progress(curriculum, completed_set)
        
        assert completed == 2
        assert total == 2
        assert pct == 100.0
    
    def test_empty_curriculum(self, service):
        """Test progress with empty curriculum."""
        completed, total, pct = service.calculate_progress([], set())
        
        assert completed == 0
        assert total == 0
        assert pct == 0.0
    
    def test_progress_with_subtopics(self, service):
        """Test progress counting subtopics."""
        curriculum = [
            {"topic": "1:Main", "subtopics": ["Sub1", "Sub2"]}
        ]
        completed_set = {"1:Main", "  ↳ Sub1"}
        
        completed, total, pct = service.calculate_progress(curriculum, completed_set)
        
        assert total == 3  # 1 main + 2 subtopics
        assert completed == 2
        assert pct == pytest.approx(66.67, rel=0.1)


class TestGetCurriculumFromUserState:
    """Tests for get_curriculum_from_user_state method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    @pytest.fixture
    def mock_user_state_simple(self):
        """Simple user state with chapters only."""
        return {
            "curriculum": [{
                "study_plan": {
                    "study_plan": [
                        {"number": 1, "name": "Introduction", "sub_topics": []},
                        {"number": 2, "name": "Basics", "sub_topics": []}
                    ]
                },
                "active_chapter": None
            }]
        }
    
    @pytest.fixture
    def mock_user_state_with_subtopics(self):
        """User state with subtopics."""
        return {
            "curriculum": [{
                "study_plan": {
                    "study_plan": [
                        {
                            "number": 1, 
                            "name": "Introduction",
                            "sub_topics": [
                                {"sub_topic": "1: Overview"},
                                {"sub_topic": "2: Getting Started"}
                            ]
                        }
                    ]
                },
                "active_chapter": {
                    "number": 1,
                    "name": "Introduction",
                    "sub_topics": [
                        {"sub_topic": "1: Overview"},
                        {"sub_topic": "2: Getting Started"}
                    ]
                }
            }]
        }
    
    def test_returns_empty_for_no_user(self, service):
        """Test returns empty list when user not found."""
        with patch('services.curriculum_service.load_user_state', return_value=None):
            result = service.get_curriculum_from_user_state("unknown_user")
            assert result == []
    
    def test_returns_empty_for_no_curriculum(self, service):
        """Test returns empty list when no curriculum."""
        with patch('services.curriculum_service.load_user_state', return_value={"curriculum": []}):
            result = service.get_curriculum_from_user_state("test_user")
            assert result == []
    
    def test_loads_simple_curriculum(self, service, mock_user_state_simple):
        """Test loading curriculum with simple chapters."""
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_simple):
            result = service.get_curriculum_from_user_state("test_user")
            
            assert len(result) == 2
            assert result[0] == "1:Introduction"
            assert result[1] == "2:Basics"
    
    def test_loads_curriculum_with_subtopics(self, service, mock_user_state_with_subtopics):
        """Test loading curriculum with subtopics."""
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_with_subtopics):
            result = service.get_curriculum_from_user_state("test_user")
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["topic"] == "1:Introduction"
            assert len(result[0]["subtopics"]) == 2
            assert "Overview" in result[0]["subtopics"][0]


class TestGetStudyMaterialForSubtopic:
    """Tests for get_study_material_for_subtopic method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    @pytest.fixture
    def mock_user_state_with_material(self):
        """User state with study material."""
        return {
            "curriculum": [{
                "active_chapter": {
                    "number": 1,
                    "name": "Biology Basics",
                    "sub_topics": [
                        {
                            "sub_topic": "Cell Structure",
                            "study_material": "Cells are the basic unit of life...",
                            "display_markdown": "# Cell Structure\n\nCells are the basic unit of life..."
                        },
                        {
                            "sub_topic": "Cell Function",
                            "study_material": "Cells perform various functions...",
                            "display_markdown": "# Cell Function\n\nCells perform various functions..."
                        }
                    ]
                }
            }]
        }
    
    def test_returns_error_for_non_subtopic(self, service):
        """Test returns error for non-subtopic."""
        result = service.get_study_material_for_subtopic("user", "1:Chapter Name")
        
        assert result.success == False
        assert "Not a subtopic" in result.error_message
    
    def test_returns_error_for_no_user(self, service):
        """Test returns error when user not found."""
        with patch('services.curriculum_service.load_user_state', return_value=None):
            result = service.get_study_material_for_subtopic("user", "  ↳ Subtopic")
            
            assert result.success == False
            assert "No curriculum found" in result.error_message
    
    def test_returns_study_material(self, service, mock_user_state_with_material):
        """Test returns study material for valid subtopic."""
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_with_material):
            result = service.get_study_material_for_subtopic("user", "  ↳ Cell Structure")
            
            assert result.success == True
            assert result.chapter_number == 1
            assert result.chapter_name == "Biology Basics"
            assert "Cell Structure" in result.subtopic_name
            assert "Cells are the basic unit" in result.study_material
    
    def test_returns_error_for_unknown_subtopic(self, service, mock_user_state_with_material):
        """Test returns error for unknown subtopic."""
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_with_material):
            result = service.get_study_material_for_subtopic("user", "  ↳ Unknown Topic")
            
            assert result.success == False
            assert "not found" in result.error_message


class TestStudyMaterialInfoDataclass:
    """Tests for StudyMaterialInfo dataclass."""
    
    def test_default_success_is_true(self):
        """Test default success value."""
        info = StudyMaterialInfo(
            chapter_number=1,
            chapter_name="Test",
            subtopic_index=0,
            subtopic_name="Sub",
            study_material="Material",
            display_markdown="# Material"
        )
        assert info.success == True
        assert info.error_message is None
    
    def test_can_set_error(self):
        """Test setting error state."""
        info = StudyMaterialInfo(
            chapter_number=0,
            chapter_name="",
            subtopic_index=-1,
            subtopic_name="",
            study_material="",
            display_markdown="",
            success=False,
            error_message="Something went wrong"
        )
        assert info.success == False
        assert info.error_message == "Something went wrong"


# =============================================================================
# Phase 2 Tests: Topic Completion
# =============================================================================

class TestMarkTopicComplete:
    """Tests for mark_topic_complete method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    @pytest.fixture
    def mock_user_state_with_subtopic(self):
        """User state with a subtopic for completion testing."""
        return {
            "curriculum": [{
                "active_chapter": {
                    "number": 1,
                    "name": "Introduction to Biology",
                    "sub_topics": [
                        {
                            "sub_topic": "Cell Structure",
                            "study_material": "Cells are the building blocks...",
                            "display_markdown": "# Cell Structure\n\nCells are...",
                            "status": "NA",
                            "quizzes": None
                        },
                        {
                            "sub_topic": "Cell Functions",
                            "study_material": "Cells perform many functions...",
                            "display_markdown": "# Cell Functions\n\nCells...",
                            "status": "NA",
                            "quizzes": None
                        }
                    ]
                },
                "study_plan": {
                    "study_plan": [
                        {
                            "number": 1,
                            "name": "Introduction to Biology",
                            "sub_topics": [
                                {"sub_topic": "Cell Structure", "status": "NA", "quizzes": None},
                                {"sub_topic": "Cell Functions", "status": "NA", "quizzes": None}
                            ]
                        }
                    ]
                }
            }]
        }
    
    def test_marks_simple_topic_complete(self, service):
        """Test marking a simple (non-subtopic) topic complete."""
        completed = set()
        unlocked = set()
        
        with patch('services.curriculum_service.load_user_state', return_value=None):
            result = service.mark_topic_complete(
                username="test_user",
                topic_name="1:Introduction",
                completed_topics=completed,
                unlocked_topics=unlocked,
                generate_quiz=False
            )
        
        assert result.success == True
        assert result.is_subtopic == False
        assert "1:Introduction" in result.completed_topics
    
    def test_marks_subtopic_complete(self, service, mock_user_state_with_subtopic):
        """Test marking a subtopic complete."""
        completed = set()
        unlocked = set()
        
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_with_subtopic), \
             patch('services.curriculum_service.save_user_state') as mock_save:
            result = service.mark_topic_complete(
                username="test_user",
                topic_name="  ↳ Cell Structure",
                completed_topics=completed,
                unlocked_topics=unlocked,
                generate_quiz=False
            )
        
        assert result.success == True
        assert result.is_subtopic == True
        assert "  ↳ Cell Structure" in result.completed_topics
        assert result.study_material is not None
        mock_save.assert_called_once()
    
    def test_uses_existing_quiz_when_available(self, service):
        """Test that existing quiz is used instead of generating new one."""
        existing_quiz = [{"question": "Q1", "choices": ["A", "B"], "answer": "A"}]
        user_state = {
            "curriculum": [{
                "active_chapter": {
                    "number": 1,
                    "name": "Test",
                    "sub_topics": [{
                        "sub_topic": "Topic1",
                        "study_material": "...",
                        "status": "NA",
                        "quizzes": existing_quiz
                    }]
                },
                "study_plan": {"study_plan": []}
            }]
        }
        
        with patch('services.curriculum_service.load_user_state', return_value=user_state), \
             patch('services.curriculum_service.save_user_state'):
            result = service.mark_topic_complete(
                username="test_user",
                topic_name="  ↳ Topic1",
                completed_topics=set(),
                unlocked_topics=set(),
                generate_quiz=True
            )
        
        assert result.quiz_data == existing_quiz
        assert result.quiz_generated == False
    
    def test_generates_quiz_when_not_exists(self, service):
        """Test quiz generation when no existing quiz."""
        user_state = {
            "curriculum": [{
                "active_chapter": {
                    "number": 1,
                    "name": "Test Chapter",
                    "sub_topics": [{
                        "sub_topic": "Topic1",
                        "study_material": "Study content...",
                        "status": "NA",
                        "quizzes": None
                    }]
                },
                "study_plan": {"study_plan": []}
            }]
        }
        generated_quiz = [{"question": "Generated Q1", "choices": ["A", "B"], "answer": "A"}]
        
        with patch('services.curriculum_service.load_user_state', return_value=user_state), \
             patch('services.curriculum_service.save_user_state'), \
             patch('services.curriculum_service.get_quiz', return_value="quiz_str"), \
             patch('services.curriculum_service.quiz_output_parser', return_value=generated_quiz):
            result = service.mark_topic_complete(
                username="test_user",
                topic_name="  ↳ Topic1",
                completed_topics=set(),
                unlocked_topics=set(),
                generate_quiz=True
            )
        
        assert result.quiz_data == generated_quiz
        assert result.quiz_generated == True
    
    def test_unlocks_next_subtopic(self, service, mock_user_state_with_subtopic):
        """Test that completing a subtopic unlocks the next one."""
        with patch('services.curriculum_service.load_user_state', return_value=mock_user_state_with_subtopic), \
             patch('services.curriculum_service.save_user_state'):
            result = service.mark_topic_complete(
                username="test_user",
                topic_name="  ↳ Cell Structure",
                completed_topics=set(),
                unlocked_topics=set(),
                generate_quiz=False
            )
        
        assert result.next_unlocked_topic == "  ↳ Cell Functions"
        assert "  ↳ Cell Functions" in result.unlocked_topics


class TestMarkTopicIncomplete:
    """Tests for mark_topic_incomplete method."""
    
    @pytest.fixture
    def service(self):
        return CurriculumService(mnt_folder="/tmp")
    
    def test_removes_from_completed(self, service):
        """Test removing topic from completed set."""
        completed = {"1:Topic1", "  ↳ Subtopic1"}
        
        new_completed, error = service.mark_topic_incomplete(
            username="test_user",
            topic_name="1:Topic1",
            completed_topics=completed
        )
        
        assert "1:Topic1" not in new_completed
        assert "  ↳ Subtopic1" in new_completed
        assert error is None
    
    def test_updates_user_state_for_subtopic(self, service):
        """Test that user state is updated when unmarking subtopic."""
        user_state = {
            "curriculum": [{
                "active_chapter": {
                    "number": 1,
                    "name": "Test",
                    "sub_topics": [{
                        "sub_topic": "Topic1",
                        "status": "COMPLETED"
                    }]
                },
                "study_plan": {"study_plan": []}
            }]
        }
        
        with patch('services.curriculum_service.load_user_state', return_value=user_state), \
             patch('services.curriculum_service.save_user_state') as mock_save:
            new_completed, error = service.mark_topic_incomplete(
                username="test_user",
                topic_name="  ↳ Topic1",
                completed_topics={"  ↳ Topic1"}
            )
        
        assert "  ↳ Topic1" not in new_completed
        mock_save.assert_called_once()


class TestTopicCompletionResultDataclass:
    """Tests for TopicCompletionResult dataclass."""
    
    def test_create_success_result(self):
        """Test creating a successful result."""
        result = TopicCompletionResult(
            success=True,
            topic_name="  ↳ Test Topic",
            is_subtopic=True,
            completed_topics={"  ↳ Test Topic"},
            unlocked_topics={"  ↳ Next Topic"}
        )
        
        assert result.success == True
        assert result.is_subtopic == True
        assert result.quiz_data is None
        assert result.error_message is None
    
    def test_create_result_with_quiz(self):
        """Test creating result with quiz data."""
        quiz = [{"question": "Q1", "answer": "A"}]
        result = TopicCompletionResult(
            success=True,
            topic_name="  ↳ Topic",
            is_subtopic=True,
            completed_topics=set(),
            unlocked_topics=set(),
            quiz_data=quiz,
            quiz_generated=True
        )
        
        assert result.quiz_data == quiz
        assert result.quiz_generated == True

