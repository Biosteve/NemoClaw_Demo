#"""
#Gradio-based Enhanced Calendar Creator with NVIDIA AI
#Web interface for creating calendar events with date/time picker and AI assistance
#"""

#import gradio as gr
## Using built-in Gradio components for better compatibility
#from datetime import datetime, timedelta
#from icalendar import Calendar, Event, vCalAddress, vText, Alarm
#import zoneinfo
#import json
#import os
#import tempfile
#import hashlib
#from pathlib import Path
#from langchain_nvidia_ai_endpoints import ChatNVIDIA
#from langchain_core.messages import SystemMessage, HumanMessage

## ===========================
## Calendar Management Functions
## ===========================

#def create_calendar_event(summary, start_datetime, duration_hours, 
#                         description="", location="", organizer_email="",
#                         organizer_name="", reminder_hours=1):
#    """Create a single calendar event and return as ICS file"""
    
#    cal = Calendar()
#    cal.add('prodid', '-//NVIDIA AI Calendar Creator//EN')
#    cal.add('version', '2.0')
#    cal.add('calscale', 'GREGORIAN')
    
#    event = Event()
#    event.add('summary', summary)
    
#    # Ensure datetime has timezone (UTC+1)
#    if start_datetime.tzinfo is None:
#        start_datetime = start_datetime.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    
#    event.add('dtstart', start_datetime)
    
#    # Calculate end time
#    end_datetime = start_datetime + timedelta(hours=duration_hours)
#    event.add('dtend', end_datetime)
    
#    # Add dtstamp (current time in UTC for compatibility)
#    event.add('dtstamp', datetime.now(zoneinfo.ZoneInfo("UTC")))
    
#    # Simple UID using timestamp and hash
#    uid_base = f"{summary}{start_datetime.isoformat()}"
#    uid_hash = hashlib.md5(uid_base.encode()).hexdigest()
#    event['uid'] = uid_hash
    
#    if location:
#        event.add('location', location)
    
#    if description:
#        event.add('description', description)
    
#    if organizer_email:
#        organizer = vCalAddress(f'mailto:{organizer_email}')
#        if organizer_name:
#            organizer.params['CN'] = organizer_name
#        event['organizer'] = organizer
    
#    # Add reminder alarm if requested
#    if reminder_hours > 0:
#        alarm = Alarm()
#        alarm.add('action', 'DISPLAY')
#        alarm.add('trigger', timedelta(hours=-reminder_hours))
#        alarm.add('description', f'Reminder: {summary}')
#        event.add_component(alarm)
    
#    cal.add_component(event)
    
#    return cal.to_ical()

#def parse_datetime_from_inputs(date_str, time_str):
#    """Parse date and time strings into datetime object"""
#    try:
#        # Handle different date formats
#        if 'T' in date_str:  # ISO format
#            dt = datetime.fromisoformat(date_str.replace('Z', '+01:00'))
#        else:
#            # Try parsing date
#            dt = datetime.strptime(date_str, '%Y-%m-%d')
        
#        # Add time if provided
#        if time_str:
#            if ':' in time_str:
#                hour, minute = map(int, time_str.split(':'))
#                dt = dt.replace(hour=hour, minute=minute)
        
#        # Add timezone (UTC+1)
#        dt = dt.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))  # UTC+1 (CET/CEST)
#        return dt
#    except Exception as e:
#        # Fallback to current time with UTC+1
#        return datetime.now(zoneinfo.ZoneInfo("Europe/Paris"))

## ===========================
## AI Integration Functions
## ===========================

#def parse_event_with_ai(user_input, api_key):
#    """Use NVIDIA AI to parse natural language into event parameters"""
    
#    if not api_key:
#        return None, "Please provide NVIDIA API key"
    
#    try:
#        llm = ChatNVIDIA(
#            model="meta/llama-3.1-405b-instruct",
#            api_key=api_key,
#            temperature=0.3,
#            max_completion_tokens=36000
#        )
        
#        current_date = datetime.now(zoneinfo.ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
#        system_prompt = f"""You are a calendar assistant. Parse user requests into structured event data.
#Return ONLY a valid JSON object with these fields:
#{{
#    "summary": "Event title",
#    "description": "Event description",
#    "start_date": "YYYY-MM-DD",
#    "start_time": "HH:MM",
#    "duration_hours": float,
#    "location": "Location (optional)",
#    "organizer_email": "email@example.com (optional)",
#    "organizer_name": "Name (optional)",
#    "reminder_hours": 1
#}}

#Current date for reference: {current_date}
#Note: All times are in UTC+1 timezone (Central European Time)

#Example input: "Schedule a team meeting tomorrow at 2pm for 2 hours about Q4 planning"
#Example output: {{"summary": "Team Meeting - Q4 Planning", "start_date": "2024-11-29", "start_time": "14:00", "duration_hours": 2.0, "description": "Quarterly planning discussion", "reminder_hours": 1}}

#IMPORTANT: Return ONLY the JSON object, no explanations.
#"""
        
#        messages = [
#            SystemMessage(content=system_prompt),
#            HumanMessage(content=user_input)
#        ]
        
#        response = llm.invoke(messages)
#        response_text = response.content.strip()
        
#        # Extract JSON
#        if '```json' in response_text:
#            start = response_text.find('```json') + 7
#            end = response_text.find('```', start)
#            response_text = response_text[start:end].strip()
#        elif '```' in response_text:
#            start = response_text.find('```') + 3
#            end = response_text.find('```', start)
#            response_text = response_text[start:end].strip()
        
#        event_data = json.loads(response_text)
#        return event_data, None
        
#    except Exception as e:
#        return None, f"Error parsing with AI: {str(e)}"

## ===========================
## Gradio Interface Functions
## ===========================

#def create_event_manual(date_value, time_str, duration, title, location, 
#                       description, organizer_name, organizer_email, reminder_hours):
#    """Create event from manual input"""
    
#    if not title:
#        return None, "❌ Please provide an event title", ""
    
#    if not date_value:
#        return None, "❌ Please select a date", ""
    
#    try:
#        # Parse datetime
#        start_dt = parse_datetime_from_inputs(date_value, time_str)
        
#        # Create ICS
#        ics_content = create_calendar_event(
#            summary=title,
#            start_datetime=start_dt,
#            duration_hours=float(duration),
#            description=description,
#            location=location,
#            organizer_email=organizer_email,
#            organizer_name=organizer_name,
#            reminder_hours=float(reminder_hours)
#        )
        
#        # Save to temp file with descriptive name
#        event_name_safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
#        filename = f"event_{event_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
#        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.ics', prefix='')
#        temp_file.write(ics_content)
#        temp_file.close()
        
#        # Format success message
#        success_msg = f"""
#✅ **Event Created Successfully!**

#📅 **Event Details:**
#- **Title:** {title}
#- **Date & Time:** {start_dt.strftime('%Y-%m-%d %H:%M')} (UTC+1)
#- **Duration:** {duration} hours
#- **Location:** {location if location else 'Not specified'}
#- **Description:** {description if description else 'Not specified'}

#📥 **How to Add to Your Calendar:**

#**Option 1 - Double-click (Easiest):**
#1. Click the **Download** button below
#2. Find the downloaded `.ics` file (usually in Downloads folder)
#3. **Double-click** the file - it should open in Outlook/Calendar automatically!

#**Option 2 - Right-click:**
#1. Right-click the downloaded `.ics` file
#2. Select **"Open with"** → Choose Outlook or your calendar app
#3. Confirm to add the event

#**Option 3 - Import manually:**
#- **Outlook:** File → Open & Export → Import/Export → Import iCalendar
#- **Google Calendar:** Settings → Import & Export → Select file
#- **Apple Calendar:** File → Import

#💡 **Tip:** The file is named `{filename}` for easy identification!
#"""
        
#        # Preview content
#        preview = ics_content.decode('utf-8')
        
#        return temp_file.name, success_msg, preview
        
#    except Exception as e:
#        return None, f"❌ Error creating event: {str(e)}", ""

#def create_event_with_ai(ai_input):
#    """Create event using AI parsing"""
    
#    if not ai_input:
#        return None, "❌ Please describe the event you want to create", ""
    
#    # Get API key from environment
#    api_key = os.environ.get('NVIDIA_API_KEY')
#    if not api_key:
#        return None, "❌ NVIDIA_API_KEY not found in environment variables. Please set it first.", ""
    
#    try:
#        # Parse with AI
#        event_data, error = parse_event_with_ai(ai_input, api_key)
        
#        if error:
#            return None, f"❌ {error}", ""
        
#        # Parse datetime
#        date_str = event_data['start_date']
#        time_str = event_data['start_time']
#        start_dt = parse_datetime_from_inputs(date_str, time_str)
        
#        # Create ICS
#        ics_content = create_calendar_event(
#            summary=event_data['summary'],
#            start_datetime=start_dt,
#            duration_hours=float(event_data['duration_hours']),
#            description=event_data.get('description', ''),
#            location=event_data.get('location', ''),
#            organizer_email=event_data.get('organizer_email', ''),
#            organizer_name=event_data.get('organizer_name', ''),
#            reminder_hours=float(event_data.get('reminder_hours', 1))
#        )
        
#        # Save to temp file with descriptive name
#        event_name_safe = "".join(c for c in event_data['summary'] if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
#        filename = f"event_{event_name_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
#        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.ics', prefix='')
#        temp_file.write(ics_content)
#        temp_file.close()
        
#        # Format success message
#        success_msg = f"""
#✅ **Event Parsed and Created Successfully!**

#🤖 **AI Interpretation:**
#```json
#{json.dumps(event_data, indent=2)}
#```

#📅 **Event Details:**
#- **Title:** {event_data['summary']}
#- **Date & Time:** {start_dt.strftime('%Y-%m-%d %H:%M')} (UTC+1)
#- **Duration:** {event_data['duration_hours']} hours
#- **Location:** {event_data.get('location', 'Not specified')}
#- **Description:** {event_data.get('description', 'Not specified')}

#📥 **How to Add to Your Calendar:**

#**Option 1 - Double-click (Easiest):**
#1. Click the **Download** button below
#2. Find the downloaded `.ics` file (usually in Downloads folder)
#3. **Double-click** the file - it should open in Outlook/Calendar automatically!

#**Option 2 - Right-click:**
#1. Right-click the downloaded `.ics` file
#2. Select **"Open with"** → Choose Outlook or your calendar app
#3. Confirm to add the event

#**Option 3 - Drag & Drop:**
#- Drag the `.ics` file directly into Outlook calendar view

#💡 **Tip:** The file is named `{filename}` for easy identification!
#"""
        
#        # Preview content
#        preview = ics_content.decode('utf-8')
        
#        return temp_file.name, success_msg, preview
        
#    except Exception as e:
#        return None, f"❌ Error creating event with AI: {str(e)}", ""

## ===========================
## Gradio Interface
## ===========================

#def create_gradio_interface():
#    """Create the Gradio web interface"""
    
#    with gr.Blocks(title="NVIDIA AI Calendar Creator", theme=gr.themes.Soft()) as app:
        
#        gr.Markdown("""
#        # 📅 NVIDIA AI Calendar Creator
        
#        Create calendar events using visual controls or natural language AI, then download as .ics files!
#        """)
        
#        with gr.Tabs() as tabs:
            
#            # ===========================
#            # Manual Entry Tab
#            # ===========================
            
#            with gr.Tab("📝 Manual Entry"):
#                gr.Markdown("""
#                ### Create events using visual date/time pickers
#                Fill in the details below and click **Create Event** to generate your calendar file.
#                """)
                
#                with gr.Row():
#                    with gr.Column(scale=2):
#                        manual_title = gr.Textbox(
#                            label="Event Title *",
#                            placeholder="e.g., Team Meeting, Doctor Appointment",
#                            lines=1
#                        )
                        
#                        with gr.Row():
#                            manual_date = gr.Textbox(
#                                label="📅 Date (YYYY-MM-DD) *",
#                                placeholder="2024-12-05",
#                                value=datetime.now().strftime("%Y-%m-%d"),
#                                info="Click to edit - format: YYYY-MM-DD (e.g., 2024-12-05)",
#                                max_lines=1
#                            )
                            
#                            manual_time = gr.Textbox(
#                                label="🕐 Time (HH:MM) - UTC+1",
#                                placeholder="14:00",
#                                value="09:00",
#                                info="24-hour format, UTC+1 timezone (e.g., 14:00 for 2pm)",
#                                max_lines=1
#                            )
                        
#                        with gr.Row():
#                            manual_duration = gr.Slider(
#                                label="⏱️ Duration (hours)",
#                                minimum=0.25,
#                                maximum=8,
#                                step=0.25,
#                                value=1.0
#                            )
                            
#                            manual_reminder = gr.Slider(
#                                label="🔔 Reminder (hours before)",
#                                minimum=0,
#                                maximum=48,
#                                step=0.25,
#                                value=1.0
#                            )
                        
#                        manual_location = gr.Textbox(
#                            label="📍 Location",
#                            placeholder="e.g., Conference Room A, 123 Main St",
#                            lines=1
#                        )
                        
#                        manual_description = gr.Textbox(
#                            label="📄 Description",
#                            placeholder="Add any additional details about the event...",
#                            lines=3
#                        )
                        
#                        with gr.Accordion("👤 Organizer Information (Optional)", open=False):
#                            manual_org_name = gr.Textbox(
#                                label="Organizer Name",
#                                placeholder="John Doe"
#                            )
#                            manual_org_email = gr.Textbox(
#                                label="Organizer Email",
#                                placeholder="john.doe@example.com"
#                            )
                        
#                        manual_create_btn = gr.Button("🎯 Create Event", variant="primary", size="lg")
                    
#                    with gr.Column(scale=1):
#                        manual_status = gr.Markdown("ℹ️ Fill in the form and click Create Event")
#                        manual_download = gr.File(label="📥 Download .ics File", visible=True)
                        
#                        with gr.Accordion("👁️ ICS Preview", open=False):
#                            manual_preview = gr.Textbox(
#                                label="ICS File Content",
#                                lines=15,
#                                max_lines=20,
#                                show_copy_button=True
#                            )
                
#                # Connect manual entry
#                manual_create_btn.click(
#                    fn=create_event_manual,
#                    inputs=[
#                        manual_date, manual_time, manual_duration,
#                        manual_title, manual_location, manual_description,
#                        manual_org_name, manual_org_email, manual_reminder
#                    ],
#                    outputs=[manual_download, manual_status, manual_preview]
#                )
            
#            # ===========================
#            # AI Assistant Tab
#            # ===========================
            
#            with gr.Tab("🤖 AI Assistant"):
#                gr.Markdown("""
#                ### Use natural language to create events
                
#                Describe your event in plain English and let AI parse the details!
                
#                **Examples:**
#                - "Schedule a team meeting tomorrow at 2pm for 2 hours"
#                - "Create a dentist appointment on December 5th at 10:30am"
#                - "Add project deadline next Friday at 5pm"
                
#                **Note:** Using API key from environment variable `NVIDIA_API_KEY`
#                """)
                
#                with gr.Row():
#                    with gr.Column(scale=2):
                        
#                        ai_input = gr.Textbox(
#                            label="📝 Describe Your Event",
#                            placeholder="e.g., Schedule a product demo next Tuesday at 3pm for 90 minutes at Conference Room B",
#                            lines=4
#                        )
                        
#                        ai_examples = gr.Examples(
#                            examples=[
#                                ["Schedule a team standup tomorrow at 9am for 30 minutes"],
#                                ["Create a client presentation on December 10th at 2pm for 2 hours"],
#                                ["Add lunch meeting with Sarah next Monday at noon"],
#                                ["Book conference room for quarterly review next Friday 3-5pm"],
#                            ],
#                            inputs=ai_input
#                        )
                        
#                        ai_create_btn = gr.Button("🚀 Create Event with AI", variant="primary", size="lg")
                    
#                    with gr.Column(scale=1):
#                        ai_status = gr.Markdown("ℹ️ Enter your event description and API key")
#                        ai_download = gr.File(label="📥 Download .ics File", visible=True)
                        
#                        with gr.Accordion("👁️ ICS Preview", open=False):
#                            ai_preview = gr.Textbox(
#                                label="ICS File Content",
#                                lines=15,
#                                max_lines=20,
#                                show_copy_button=True
#                            )
                
#                # Connect AI assistant (pass None as api_key parameter, will use env var)
#                ai_create_btn.click(
#                    fn=create_event_with_ai,
#                    inputs=[ai_input],
#                    outputs=[ai_download, ai_status, ai_preview]
#                )
            
#            # ===========================
#            # Help Tab
#            # ===========================
            
#            with gr.Tab("ℹ️ Help & Import Guide"):
#                gr.Markdown("""
#                ## 📚 How to Use This App
                
#                ### Manual Entry Mode
#                1. Select a date (YYYY-MM-DD format)
#                2. Enter time in HH:MM format (24-hour, UTC+1 timezone)
#                3. Set duration and reminder time with sliders
#                4. Fill in event details (title is required)
#                5. Click **Create Event**
#                6. Download the .ics file
                
#                **Note:** All times are in UTC+1 (Central European Time)
                
#                ### AI Assistant Mode
#                1. Ensure `NVIDIA_API_KEY` environment variable is set
#                2. Describe your event in natural language
#                3. Click **Create Event with AI**
#                4. Review the parsed details
#                5. Download the .ics file
                
#                **Setting API Key:**
#                - PowerShell: `$env:NVIDIA_API_KEY="nvapi-xxxxx"`
#                - Get your key from [build.nvidia.com](https://build.nvidia.com/)
                
#                ---
                
#                ## 📥 How to Import to Your Calendar
                
#                ### 🎯 EASIEST METHOD - Just Double-Click!
                
#                After downloading the `.ics` file:
#                1. Go to your **Downloads** folder
#                2. Find the `.ics` file (named like `event_Team_Meeting_20241128_123456.ics`)
#                3. **Double-click** the file
#                4. Your default calendar app (Outlook, Calendar) will open automatically
#                5. Click **Save** or **Add to Calendar** in the prompt
                
#                **That's it!** The event is now in your calendar.
                
#                ---
                
#                ### Alternative Methods
                
#                ### Google Calendar
#                1. Open [Google Calendar](https://calendar.google.com/)
#                2. Click the **gear icon** → **Settings**
#                3. Select **Import & Export** from the left menu
#                4. Click **Select file from your computer**
#                5. Choose your downloaded .ics file
#                6. Select which calendar to add it to
#                7. Click **Import**
                
#                ### Microsoft Outlook
                
#                **Outlook Desktop:**
#                1. Open Outlook
#                2. Go to **File** → **Open & Export** → **Import/Export**
#                3. Select **Import an iCalendar (.ics) or vCalendar file**
#                4. Browse to your .ics file
#                5. Click **OK**
                
#                **Outlook Web:**
#                1. Open [Outlook.com](https://outlook.com/)
#                2. Click the **calendar icon**
#                3. Click **Add calendar** → **Upload from file**
#                4. Choose your .ics file
#                5. Click **Import**
                
#                ### Apple Calendar (macOS/iOS)
                
#                **macOS:**
#                1. Open Calendar app
#                2. Go to **File** → **Import**
#                3. Select your .ics file
#                4. Choose which calendar to add it to
#                5. Click **Import**
                
#                **iOS:**
#                1. Open the .ics file in Mail or Files
#                2. Tap the file
#                3. Tap **Add to Calendar**
#                4. Confirm the import
                
#                ### Other Calendar Apps
#                Most calendar applications support .ics files:
#                - Thunderbird: **Events and Tasks** → **Import**
#                - CalDAV apps: Usually have an **Import** option
#                - Mobile apps: Often can import from Files/Downloads
                
#                ---
                
#                ## 🔧 Troubleshooting
                
#                **Date picker not working?**
#                - Make sure JavaScript is enabled in your browser
#                - Try refreshing the page
                
#                **AI not parsing correctly?**
#                - Be specific with dates and times
#                - Use formats like "tomorrow", "December 5th", "next Monday"
#                - Include duration: "for 2 hours", "for 90 minutes"
                
#                **Can't import .ics file?**
#                - **Try double-clicking** the downloaded .ics file first
#                - If that doesn't work, **right-click** → **Open with** → Select Outlook/Calendar
#                - For Outlook: Make sure Outlook is set as default for `.ics` files
#                - Verify the file downloaded completely (check file size > 0)
#                - Check that your calendar app supports .ics format
#                - Try opening the file in a text editor to verify it's valid
                
#                **API key not working?**
#                - Verify `NVIDIA_API_KEY` environment variable is set
#                - Check it starts with "nvapi-"
#                - Ensure you have API credits at [build.nvidia.com](https://build.nvidia.com/)
#                - Restart the app after setting environment variable
                
#                ---
                
#                ## 🎯 Features
                
#                ✅ Visual date/time picker with Flatpickr  
#                ✅ Natural language AI parsing (NVIDIA Llama 3.1 405B)  
#                ✅ Standard RFC 5545 iCalendar format  
#                ✅ Compatible with all major calendar apps  
#                ✅ Reminders and alarms  
#                ✅ Organizer information  
#                ✅ Location and description fields  
#                ✅ Web-based - no installation needed  
                
#                ---
                
#                ## 🔗 Resources
                
#                - [NVIDIA AI Endpoints](https://build.nvidia.com/)
#                - [iCalendar Specification](https://icalendar.org/)
#                - [Google Calendar Help](https://support.google.com/calendar/)
#                - [Outlook Help](https://support.microsoft.com/outlook)
                
#                ---
                
#                **Made with ❤️ using Gradio, NVIDIA AI, and Python**
#                """)
        
#        gr.Markdown("""
#        ---
#        💡 **Tip:** You can create multiple events - just download each .ics file separately and import them all!
#        """)
    
#    return app

## ===========================
## Main Entry Point
## ===========================

#if __name__ == "__main__":
#    app = create_gradio_interface()
    
#    # Launch with options
#    app.launch(
#        share=False,  # Set to True to create a public link
#        server_name="0.0.0.0",  # Allow external access
#        server_port=7860,
#        show_error=True
#    )
