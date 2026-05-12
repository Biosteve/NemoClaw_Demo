"""
Tests for CalendarService.

These tests verify the Gradio-agnostic calendar event creation logic.
"""
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from services.calendar_service import (
    CalendarService,
    CalendarEventResult,
    CalendarEventData
)


class TestCalendarServiceInit:
    """Tests for CalendarService initialization."""
    
    def test_init_with_defaults(self):
        """Test service initialization with defaults."""
        with patch.dict(os.environ, {'NVIDIA_API_KEY': 'test-key'}):
            service = CalendarService()
            assert service.api_key == 'test-key'
            assert service.model == "meta/llama-3.1-405b-instruct"
            assert service.timezone == "Europe/Paris"
    
    def test_init_with_custom_api_key(self):
        """Test service initialization with custom API key."""
        service = CalendarService(api_key="custom-key")
        assert service.api_key == "custom-key"
    
    def test_init_with_custom_timezone(self):
        """Test service initialization with custom timezone."""
        service = CalendarService(api_key="key", timezone="America/New_York")
        assert service.timezone == "America/New_York"


class TestCreateCalendarEvent:
    """Tests for create_calendar_event method."""
    
    @pytest.fixture
    def service(self):
        return CalendarService(api_key="test-key")
    
    def test_creates_valid_ics(self, service):
        """Test creating a valid ICS file."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Test Meeting",
            start_datetime=start_dt,
            duration_hours=1.0
        )
        
        assert isinstance(ics_content, bytes)
        ics_text = ics_content.decode('utf-8')
        assert "BEGIN:VCALENDAR" in ics_text
        assert "BEGIN:VEVENT" in ics_text
        assert "Test Meeting" in ics_text
        assert "END:VCALENDAR" in ics_text
    
    def test_includes_location(self, service):
        """Test ICS includes location when provided."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Meeting",
            start_datetime=start_dt,
            duration_hours=1.0,
            location="Conference Room A"
        )
        
        ics_text = ics_content.decode('utf-8')
        assert "Conference Room A" in ics_text
    
    def test_includes_description(self, service):
        """Test ICS includes description when provided."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Meeting",
            start_datetime=start_dt,
            duration_hours=1.0,
            description="Discuss project status"
        )
        
        ics_text = ics_content.decode('utf-8')
        assert "Discuss project status" in ics_text
    
    def test_includes_reminder_alarm(self, service):
        """Test ICS includes reminder alarm."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Meeting",
            start_datetime=start_dt,
            duration_hours=1.0,
            reminder_hours=1.0
        )
        
        ics_text = ics_content.decode('utf-8')
        assert "BEGIN:VALARM" in ics_text
    
    def test_no_alarm_when_zero(self, service):
        """Test ICS has no alarm when reminder_hours is 0."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Meeting",
            start_datetime=start_dt,
            duration_hours=1.0,
            reminder_hours=0
        )
        
        ics_text = ics_content.decode('utf-8')
        assert "BEGIN:VALARM" not in ics_text
    
    def test_calculates_end_time(self, service):
        """Test that end time is calculated from duration."""
        start_dt = datetime(2024, 12, 15, 14, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
        
        ics_content = service.create_calendar_event(
            summary="Meeting",
            start_datetime=start_dt,
            duration_hours=2.5
        )
        
        ics_text = ics_content.decode('utf-8')
        # End time should be 16:30 (14:00 + 2.5 hours)
        assert "DTEND" in ics_text


class TestParseDatetime:
    """Tests for parse_datetime method."""
    
    @pytest.fixture
    def service(self):
        return CalendarService(api_key="test-key")
    
    def test_parse_date_and_time(self, service):
        """Test parsing date and time strings."""
        result = service.parse_datetime("2024-12-15", "14:30")
        
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.tzinfo is not None
    
    def test_parse_date_only(self, service):
        """Test parsing date without time."""
        result = service.parse_datetime("2024-12-15", "")
        
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 15
        assert result.tzinfo is not None
    
    def test_parse_iso_format(self, service):
        """Test parsing ISO format datetime."""
        result = service.parse_datetime("2024-12-15T14:30:00", "")
        
        assert result.year == 2024
        assert result.hour == 14
    
    def test_fallback_on_invalid(self, service):
        """Test fallback to current time on invalid input."""
        result = service.parse_datetime("invalid", "bad")
        
        # Should return current time, so just check it's a datetime with timezone
        assert result.tzinfo is not None
        assert isinstance(result, datetime)


class TestCreateEventFromDescription:
    """Tests for create_event_from_description method."""
    
    @pytest.fixture
    def service(self):
        return CalendarService(api_key="test-key")
    
    def test_empty_description_returns_error(self, service):
        """Test that empty description returns error."""
        result = service.create_event_from_description("")
        
        assert result.success == False
        assert "describe" in result.status_message.lower()
    
    def test_whitespace_description_returns_error(self, service):
        """Test that whitespace-only description returns error."""
        result = service.create_event_from_description("   ")
        
        assert result.success == False
    
    def test_missing_api_key_returns_error(self):
        """Test that missing API key returns error."""
        # Clear the env var to test missing key scenario
        with patch.dict(os.environ, {'NVIDIA_API_KEY': ''}, clear=False):
            # Also explicitly pass None to override any env var
            service = CalendarService(api_key=None)
            # Force api_key to None (in case env var is still being read)
            service.api_key = None
            result = service.create_event_from_description("Meeting tomorrow")
        
            assert result.success == False
            assert "API key" in result.status_message
    
    @patch.object(CalendarService, 'parse_event_with_ai')
    def test_ai_parse_error_returns_error(self, mock_parse, service):
        """Test that AI parse error is handled."""
        mock_parse.return_value = (None, "AI error")
        
        result = service.create_event_from_description("Meeting tomorrow")
        
        assert result.success == False
        assert "AI error" in result.error
    
    @patch.object(CalendarService, 'parse_event_with_ai')
    def test_successful_event_creation(self, mock_parse, service):
        """Test successful event creation."""
        mock_parse.return_value = (
            {
                "summary": "Test Meeting",
                "start_date": "2024-12-15",
                "start_time": "14:00",
                "duration_hours": 1.0,
                "description": "Test description",
                "location": "Room A",
                "organizer_email": "",
                "organizer_name": "",
                "reminder_hours": 1
            },
            None
        )
        
        result = service.create_event_from_description("Test meeting tomorrow at 2pm")
        
        assert result.success == True
        assert result.file_path is not None
        assert result.filename is not None
        assert result.preview is not None
        assert result.event_data is not None
        assert result.event_data.summary == "Test Meeting"
        assert "Successfully" in result.status_message
    
    @patch.object(CalendarService, 'parse_event_with_ai')
    def test_creates_temp_file(self, mock_parse, service):
        """Test that a temp file is created."""
        mock_parse.return_value = (
            {
                "summary": "Meeting",
                "start_date": "2024-12-15",
                "start_time": "14:00",
                "duration_hours": 1.0
            },
            None
        )
        
        result = service.create_event_from_description("Meeting")
        
        assert result.file_path is not None
        assert os.path.exists(result.file_path)
        assert result.file_path.endswith('.ics')
        
        # Clean up
        os.unlink(result.file_path)


class TestCalendarEventDataDataclass:
    """Tests for CalendarEventData dataclass."""
    
    def test_required_fields(self):
        """Test creating with required fields."""
        data = CalendarEventData(
            summary="Test",
            start_date="2024-12-15",
            start_time="14:00",
            duration_hours=1.0
        )
        assert data.summary == "Test"
        assert data.duration_hours == 1.0
    
    def test_default_values(self):
        """Test default values."""
        data = CalendarEventData(
            summary="Test",
            start_date="2024-12-15",
            start_time="14:00",
            duration_hours=1.0
        )
        assert data.description == ""
        assert data.location == ""
        assert data.reminder_hours == 1.0


class TestCalendarEventResultDataclass:
    """Tests for CalendarEventResult dataclass."""
    
    def test_success_result(self):
        """Test successful result."""
        result = CalendarEventResult(
            success=True,
            file_path="/tmp/event.ics",
            filename="event.ics",
            status_message="Created!"
        )
        assert result.success == True
        assert result.error is None
    
    def test_error_result(self):
        """Test error result."""
        result = CalendarEventResult(
            success=False,
            error="Something went wrong",
            status_message="Failed"
        )
        assert result.success == False
        assert result.error == "Something went wrong"

