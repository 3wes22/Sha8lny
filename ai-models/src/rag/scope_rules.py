"""
Advisor Scope Rules and System Prompts

Defines what the career advisor should and should not help with,
and provides the system prompt for the LLM.
"""

from typing import List, Tuple
import re


# ============================================================================
# SCOPE DEFINITIONS
# ============================================================================

# Topics the advisor SHOULD help with
IN_SCOPE_TOPICS = [
    # Career Development
    "career path planning",
    "career transition advice",
    "job search strategies",
    "resume and CV writing",
    "portfolio building",
    "personal branding",
    "networking strategies",
    "salary negotiation",
    "interview preparation",
    "job offer evaluation",
    
    # Learning & Skill Development
    "how to learn programming for a job",
    "technology roadmaps for careers",
    "skill gap analysis",
    "course and resource recommendations",
    "learning plan creation",
    "study strategies",
    "time management for learning",
    "certification advice",
    
    # Industry Knowledge
    "tech industry trends",
    "job market insights",
    "company research",
    "role comparisons",
    "salary expectations",
    "remote work guidance",
    
    # Professional Growth
    "career progression paths",
    "promotion preparation",
    "leadership development",
    "soft skills development",
    "work-life balance",
    "dealing with workplace challenges",
    
    # Egyptian Market Specific
    "Egyptian tech job market",
    "companies hiring in Egypt",
    "remote work from Egypt",
    "freelancing in Egypt",
]

# Topics the advisor should NOT help with (redirect politely)
OUT_OF_SCOPE_TOPICS = [
    # Coding/Technical Implementation
    "how to implement algorithms",
    "debugging specific code",
    "syntax errors",
    "code review",
    "specific programming problems",
    "homework solutions",
    "coding exercises",
    
    # Non-Career Topics  
    "personal relationships",
    "health advice",
    "financial investment",
    "legal advice",
    "political opinions",
    "religious guidance",
    
    # Tool/Platform Specific
    "specific IDE configuration",
    "specific library API details",
    "detailed documentation lookup",
    
    # Out of Domain
    "topics unrelated to career/learning",
    "entertainment recommendations",
    "news and current events",
]


# Keywords that suggest coding help (should be redirected)
CODING_HELP_PATTERNS = [
    r"\b(implement|code|write|program|debug|fix|error|bug|syntax)\b.*\b(function|class|method|loop|array|list|algorithm)\b",
    r"\bhow (do|can) (I|you) (write|code|implement|create)\b",
    r"\b(recursion|sorting|linked list|binary tree|hash table|graph)\b.*\b(in|using|with)\s+(python|javascript|java|c\+\+|cpp)\b",
    r"\b(print|return|output|display)\b.*\b(tree|array|list|matrix)\b",
    r"\bwhat('s| is) (wrong|the error|the bug)\b",
    r"\b(TypeError|ValueError|SyntaxError|AttributeError|IndexError)\b",
    r"\bcode (doesn't|does not|won't|isn't) (work|run|compile)\b",
]

# Keywords that suggest career-related questions
CAREER_KEYWORDS = [
    "job", "career", "work", "hire", "hiring", "employ", "interview",
    "resume", "cv", "salary", "company", "companies", "role", "position",
    "learn", "study", "course", "roadmap", "path", "transition", "switch",
    "skill", "portfolio", "project", "experience", "junior", "senior",
    "remote", "freelance", "intern", "internship", "offer", "negotiate",
    "promotion", "manager", "lead", "team", "workplace", "growth",
    "industry", "market", "trend", "demand", "egypt", "cairo",
]


# ============================================================================
# SCOPE CHECKING FUNCTIONS
# ============================================================================

def is_coding_help_request(message: str) -> bool:
    """
    Check if the message is asking for coding/implementation help.
    
    These should be redirected to career-focused advice instead.
    """
    message_lower = message.lower()
    
    for pattern in CODING_HELP_PATTERNS:
        if re.search(pattern, message_lower):
            return True
    
    return False


def is_career_related(message: str) -> bool:
    """
    Check if the message is related to careers/learning.
    
    Returns True if the message contains career-related keywords.
    """
    message_lower = message.lower()
    
    for keyword in CAREER_KEYWORDS:
        if keyword in message_lower:
            return True
    
    return False


def classify_message(message: str) -> Tuple[str, str]:
    """
    Classify a user message based on scope.
    
    Returns:
        (classification, redirect_hint)
        
        classification: 'in_scope', 'coding_redirect', 'unclear', 'out_of_scope'
        redirect_hint: Suggestion for how to redirect (if applicable)
    """
    message_lower = message.lower().strip()
    
    # Very short or unclear messages
    if len(message_lower) < 10:
        return ('unclear', 'Ask clarifying question about what career topic they need help with')
    
    # Check for coding help requests
    if is_coding_help_request(message):
        return ('coding_redirect', 'Redirect to how to learn this skill for a job')
    
    # Check if career-related
    if is_career_related(message):
        return ('in_scope', '')
    
    # If not clearly career-related, ask for clarification
    return ('unclear', 'Ask how this relates to their career goals')


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a career advisor AI assistant for Sha8alny, an Egyptian career development platform. Your role is to provide helpful, actionable career guidance focused on the tech industry, especially relevant to the Egyptian job market.

## Your Expertise
- Career planning and path development
- Job search strategies and interview preparation  
- Learning roadmaps for tech skills (with focus on landing jobs, not just theory)
- Egyptian tech job market insights
- Resume/CV and portfolio advice
- Salary negotiation guidance
- Professional development and growth

## Your Personality
- Supportive and encouraging but realistic
- Direct and actionable, not vague
- Knowledgeable about Egyptian tech industry
- Professional but approachable
- Focused on practical outcomes

## Response Guidelines

### DO:
- Give specific, actionable advice
- Relate everything back to career outcomes
- Provide step-by-step guidance when appropriate
- Reference Egyptian market specifics when relevant
- Encourage realistic timelines and expectations
- Ask clarifying questions when needed

### DON'T:
- Help with specific coding implementations or debugging
- Provide answers to homework or coding exercises
- Give advice on non-career topics
- Make promises about job guarantees
- Recommend specific companies to apply for (they should research)
- Provide legal, financial, or medical advice

## Handling Out-of-Scope Requests

### For coding help requests:
If someone asks "How do I implement recursion in Python?" respond:
"I focus on career guidance rather than coding implementation. However, I'd be happy to help you understand how to learn recursion effectively for landing a job, or suggest learning resources for Python programming. What's your career goal with Python?"

### For unclear questions:
Ask for clarification:
"I'd be happy to help! Could you tell me more about what you're trying to achieve career-wise? For example:
- Are you looking to learn this skill for a specific role?
- Is this related to interview preparation?
- Are you exploring career options?"

### For off-topic requests:
Politely redirect:
"I'm specifically designed to help with tech career guidance. If you have questions about job searching, skill development, or career planning, I'm here to help!"

## Context Usage
When provided with context about the user's profile, roadmap, or assessments, reference this information to personalize your advice. Make the user feel that you understand their specific situation.

## Response Format
- Keep responses focused and concise (200-400 words ideal)
- Use bullet points for lists and steps
- Bold important points
- Provide a clear call-to-action or next step when appropriate
"""


CLARIFYING_QUESTIONS = [
    "I'd be happy to help! Could you tell me more about what specific career topic you'd like to discuss?",
    "I want to make sure I give you the best advice. What's your main career goal right now?",
    "Could you provide more context about your situation? For example, are you a student, job seeker, or looking to transition careers?",
    "I'd like to understand your situation better. What role or career path are you interested in?",
    "What specifically would you like help with - job searching, learning a skill, interview prep, or something else?",
]


CODING_REDIRECT_TEMPLATES = [
    "I focus on career guidance rather than coding implementation. However, I'd be happy to help you understand **how to learn {topic} effectively for landing a job**. What role are you targeting?",
    "Great question about {topic}! While I can't help with specific code, I can guide you on **the best approach to learning {topic} for your career goals**. What kind of job are you aiming for?",
    "I specialize in career advice, so I'll redirect this a bit. If you want to use {topic} professionally, let me help you with **a learning roadmap that leads to job opportunities**. What's your career goal?",
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_redirect_response(message: str) -> str:
    """Generate a redirect response for coding help requests."""
    import random
    
    # Try to extract the topic
    topic = "this skill"  # default
    
    # Common topics to detect
    topic_patterns = [
        (r"\b(python|javascript|java|c\+\+|cpp|go|rust|typescript)\b", "{}"),
        (r"\b(react|angular|vue|django|flask|node|express)\b", "{}"),
        (r"\b(recursion|sorting|algorithms|data structures)\b", "{}"),
        (r"\b(machine learning|ml|ai|deep learning)\b", "AI/ML"),
        (r"\b(sql|database|mongodb|postgresql)\b", "databases"),
    ]
    
    for pattern, replacement in topic_patterns:
        match = re.search(pattern, message.lower())
        if match:
            topic = replacement.format(match.group(1)) if '{}' in replacement else replacement
            break
    
    template = random.choice(CODING_REDIRECT_TEMPLATES)
    return template.format(topic=topic)


def get_clarifying_question() -> str:
    """Get a random clarifying question."""
    import random
    return random.choice(CLARIFYING_QUESTIONS)


# Simple test
if __name__ == "__main__":
    test_messages = [
        "How do I become a software engineer?",  # in_scope
        "How do I implement binary search in Python?",  # coding_redirect
        "help",  # unclear
        "What should I learn to get a job?",  # in_scope
        "How to print a tree in cpp?",  # coding_redirect
        "What's the best career for me?",  # in_scope
    ]
    
    print("Testing scope classification:\n")
    for msg in test_messages:
        classification, hint = classify_message(msg)
        print(f"'{msg}'")
        print(f"  → {classification}")
        if hint:
            print(f"  → Hint: {hint}")
        print()
