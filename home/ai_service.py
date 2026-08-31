import os
import json
import logging
import requests
from django.conf import settings
from home.models import Courses, Pages, Qualifications

logger = logging.getLogger(__name__)

# Fallback list of models supported by Gemini API
GEMINI_MODELS = [
    'gemini-flash-latest',
    'gemini-2.0-flash',
    'gemini-3.5-flash',
    'gemini-pro-latest'
]

def get_api_key():
    """Retrieve Gemini API key from environment or settings."""
    return (
        os.environ.get("AI_API_KEY") or 
        os.environ.get("GEMINI_API_KEY") or 
        getattr(settings, "AI_API_KEY", None) or 
        getattr(settings, "GEMINI_API_KEY", None)
    )

def build_seminary_context():
    """
    Dynamically extract seminary courses, pages, and key details from database
    to provide the AI model with exhaustive, concentrated, accurate real-time knowledge.
    """
    # Active courses mapping
    courses_info = []
    try:
        courses = Courses.objects.filter(status=1, deleted_at__isnull=True).select_related('highest_qualification').order_by('id')
        for c in courses:
            fees_text = f"${c.fees:,.2f}" if c.fees is not None else "Contact Admissions for current fee schedule & scholarships"
            courses_info.append(
                f"1. [**{c.course_name}**](/courses/{c.course_code}/) (Code: `{c.course_code}`)\n"
                f"   - **Credits:** {c.credit_hours} Credit Hours\n"
                f"   - **Tuition/Fees:** {fees_text}\n"
                f"   - **Direct Link:** [View {c.course_name} Details](/courses/{c.course_code}/)"
            )
    except Exception as e:
        logger.warning(f"Error querying courses for AI context: {e}")
        courses_info = [
            "1. [**Introduction to Bible**](/courses/ADBS/) (Code: `ADBS` | 100 Credit Hours | $100.00 | Link: [View Details](/courses/ADBS/))",
            "2. [**Certificate in Theology (C.Th.)**](/courses/CTH/) (Code: `CTH` | 50 Credit Hours | Link: [View Details](/courses/CTH/))",
            "3. [**Associate Degree in Theology (A.Th.)**](/courses/ATH/) (Code: `ATH` | 50 Credit Hours | Link: [View Details](/courses/ATH/))",
            "4. [**Bachelor of Theology (B.Th.)**](/courses/BTH/) (Code: `BTH` | 110 Credit Hours | Link: [View Details](/courses/BTH/))",
            "5. [**Master of Divinity (M.Div.)**](/courses/MDIV/) (Code: `MDIV` | 80 Credit Hours | $1,010.00 | Link: [View Details](/courses/MDIV/))",
            "6. [**Master of Theology (M.Th.)**](/courses/MTH/) (Code: `MTH` | 70 Credit Hours | Link: [View Details](/courses/MTH/))",
            "7. [**Doctor of Ministry (D.Min.)**](/courses/DMIN/) (Code: `DMIN` | 80 Credit Hours | Link: [View Details](/courses/DMIN/))"
        ]

    # Key Seminary institutional pages
    pages_info = []
    try:
        pages = Pages.objects.filter(deleted_at__isnull=True)
        if hasattr(Pages, 'status'):
            pages = pages.filter(status=1)
        for p in pages:
            if "test" in p.code.lower():
                continue
            pages_info.append(f"- [**{p.title}**](/page/{p.code}/) (Link: `/page/{p.code}/`)")
    except Exception as e:
        logger.warning(f"Error querying pages for AI context: {e}")

    context_str = f"""
===================================================================
TRINITY THEOLOGICAL SEMINARY - COMPLETE KNOWLEDGE BASE
===================================================================

### ABOUT TRINITY THEOLOGICAL SEMINARY:
Trinity Theological Seminary is an esteemed Christian theological institution providing rigorous, sound biblical education, practical ministry leadership, and theological scholarship. We train pastors, church leaders, evangelists, missionaries, and Christian workers globally.

### COMPLETE LIST OF ALL ACTIVE COURSES (ALL 7 PROGRAMS):
{chr(10).join(courses_info)}

### CORE INSTITUTIONAL PAGES & GUIDES:
- [**Admission Process**](/page/Admission-Process/): Step-by-step guidance on entry requirements and enrolment.
- [**Fees Structure**](/page/Fees-Structure/): Detailed breakdown of tuition, credits, and payment plans.
- [**Scholarship Opportunities**](/page/Scholarship/): Financial assistance and scholarship programs.
- [**Accreditation**](/page/Accreditation/): Institutional accreditation and academic standing.
- [**About Us**](/page/about-us/): Our history, vision, statement of faith, and mission.
- [**Founder's Message**](/page/message-from-the-founder/): Vision and welcome from our founder.
- [**Church Partnership Program**](/page/church-partnership-program/): Equipping local congregations and ministry leaders.
- [**Certificate Program Overview**](/page/certificate-program/)
- [**Associate Program Overview**](/page/associate-program/)
- [**Bachelors Program Overview**](/page/bachelors-program/)
- [**Masters Programs Overview**](/page/masters-programs/)
- [**Doctoral Program Overview**](/page/doctoral-program/)

### CRITICAL ACTIONABLE LINKS:
- **Online Student Application / Registration**: [Apply & Register Online](/register/)
- **Full Courses Catalog**: [Browse All Courses](/course-list/)
- **Contact & Admissions Office**: [Contact Us](/contact-us/)
- **Student & Faculty Login**: [Student Portal Sign In](/signin/)
- **Student Reference Form**: [Submit Reference Form](/reference-form/)
- **Tuition & Registration Payment**: [Make Payment](/make-payment/)
- **Church Admin Registration**: [Church Partner Registration](/church-admin/register/)
- **Guest Student Registration**: [Guest Registration](/guest/register/)

### ADMISSIONS WORKFLOW (How a student applies):
1. **Explore Courses**: Prospective students view options at [Browse All Courses](/course-list/).
2. **Submit Application**: Fill the online application at [Register Online](/register/).
3. **Reference Verification**: Submit pastoral/academic references through the [Reference Form](/reference-form/).
4. **Tuition Payment**: Complete enrollment and fee submission via [Make Payment](/make-payment/).
5. **Access LMS**: Log in at [Sign In](/signin/) to begin studies online or on-campus.
"""
    return context_str


def get_system_prompt():
    """Build the full system instructions for the AI Chatbot."""
    seminary_data = build_seminary_context()
    return f"""You are the official "Trinity Representative" for Trinity Theological Seminary.
Your tone must ALWAYS be professional, warm, courteous, encouraging, and highly helpful.

Knowledge Base:
{seminary_data}

CRITICAL RULES:
1. **Continuous Multi-Turn Support**: Maintain full context of previous messages in the conversation chain so you can answer follow-up questions accurately.
2. **Exhaustive & Concentrated Course Listings**: When asked to list courses or what programs are offered, you MUST list ALL 7 active courses (Introduction to Bible, Certificate in Theology, Associate Degree in Theology, Bachelor of Theology, Master of Divinity, Master of Theology, Doctor of Ministry) in a clean, concentrated format with their Course Code, Credits, Tuition info, and their direct clickable link (e.g., [Introduction to Bible](/courses/ADBS/)). Do NOT omit any course.
3. **Relevant Inline Links**: Whenever you mention any course, degree, admission step, form, page, or contact detail, embed the exact clickable markdown link right in the text (e.g. [Bachelor of Theology (B.Th.)](/courses/BTH/), [Apply Online](/register/), [Admission Process](/page/Admission-Process/), [Contact Us](/contact-us/), [Make Payment](/make-payment/)).
4. **Accurate Trinity Details**: When asked about any topic related to Trinity Seminary (fees, scholarships, accreditation, church partnerships, admissions, founder's message), provide thorough, accurate, concentrated responses with direct links.
5. **Professional Presentation**: Use clean markdown with clear headings, bullet points, and bold terms for maximum readability.
"""


def generate_chat_reply(user_message, history=None):
    """
    Call Gemini API with multi-turn conversation support.
    
    :param user_message: str - The user's input question
    :param history: list - List of previous chat dicts [{'role': 'user'|'model', 'text': '...'}]
    :return: dict with 'reply': str, 'success': bool, 'error': str (optional)
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "API key is not configured in .env",
            "reply": "Thank you for reaching out to Trinity Theological Seminary. For immediate assistance, please explore our [Course Catalog](/course-list/) or get in touch with our admissions team at [Contact Us](/contact-us/)."
        }

    system_instruction = get_system_prompt()

    # Build Gemini API contents payload with valid alternating user/model turns
    contents = []
    
    if history and isinstance(history, list):
        # Clean history to ensure strict alternating user -> model sequence
        expected_role = "user"
        for msg in history[-14:]:  # last 14 messages for rich context
            raw_role = msg.get("role", "user")
            role = "user" if raw_role == "user" else "model"
            text_content = msg.get("text") or msg.get("content") or ""
            if text_content.strip():
                if role == expected_role:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text_content.strip()}]
                    })
                    expected_role = "model" if expected_role == "user" else "user"
                elif contents and role != expected_role:
                    # Append text to previous turn if repeated
                    contents[-1]["parts"][0]["text"] += "\n" + text_content.strip()

    # If the last entry in contents was 'user', append this message to it or ensure alternating
    if contents and contents[-1]["role"] == "user":
        contents.pop()  # Replace with latest unified message or append

    # Add current user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message.strip()}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    last_error = None
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        reply_text = parts[0].get("text", "").strip()
                        return {
                            "success": True,
                            "reply": reply_text,
                            "model": model_name
                        }
            else:
                last_error = f"Model {model_name} returned status {response.status_code}: {response.text[:200]}"
                logger.warning(last_error)
                continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            logger.warning(f"Request error calling {model_name}: {e}")
            continue

    logger.error(f"All AI models failed. Last error: {last_error}")
    return {
        "success": False,
        "error": last_error,
        "reply": (
            "Thank you for contacting Trinity Theological Seminary! We are pleased to assist you. "
            "Please explore our complete [Course Catalog](/course-list/), review our [Admission Process](/page/Admission-Process/), "
            "or contact our admissions office directly at [Contact Us](/contact-us/)."
        )
    }
