"""
Tag system for AI Tools Wiki Bot.
Combines predefined core tags with user-voted community tags.
"""

# Core predefined tags (always available)
CORE_TAGS = [
    # Primary use cases
    'code-assistant',
    'search-engine', 
    'chatbot',
    'content-creation',
    'data-analysis',
    'design-tool',
    'productivity',
    'learning',
    
    # Target users
    'developer',
    'researcher', 
    'business',
    'student',
    'creative',
    
    # Integration types
    'api-available',
    'no-code',
    'open-source',
    'browser-based',
    'mobile-app',
    
    # Specializations
    'language-model',
    'image-generation',
    'code-generation',
    'real-time-data',
    'automation',
    'voice-ai'
]

# Tag descriptions for AI to understand when to use each tag
TAG_DESCRIPTIONS = {
    'code-assistant': 'Tools that help with programming, debugging, code generation, pair programming',
    'search-engine': 'AI-powered search and information retrieval tools',
    'chatbot': 'Conversational AI for general purposes, Q&A, assistance',
    'content-creation': 'Writing, copywriting, marketing content, blog posts, documentation',
    'data-analysis': 'Analytics, reporting, data insights, visualization tools',
    'design-tool': 'UI/UX design, graphics, creative visual tools, prototyping',
    'productivity': 'Task management, workflow automation, efficiency tools, scheduling',
    'learning': 'Educational tools, training, skill development, tutorials',
    'developer': 'Targeted at software developers, engineers, programmers',
    'researcher': 'Academic research, scientific analysis, literature review tools',
    'business': 'Enterprise and professional business applications, management',
    'student': 'Educational use, academic assistance, homework help',
    'creative': 'For artists, designers, content creators, writers',
    'api-available': 'Offers programmatic API access for integration',
    'no-code': 'User-friendly GUI, no technical skills required',
    'open-source': 'Open source projects and tools, free to use/modify',
    'browser-based': 'Web-based applications, no installation required',
    'mobile-app': 'Has mobile app versions available',
    'language-model': 'Based on large language models (LLM), text generation',
    'image-generation': 'AI art, visual content creation, graphics generation',
    'code-generation': 'Automated code writing and generation, scaffolding',
    'real-time-data': 'Access to live, current information, real-time updates',
    'automation': 'Workflow automation, task scheduling, process optimization',
    'voice-ai': 'Speech recognition, voice synthesis, audio processing'
}

def get_all_available_tags():
    """
    Get all available tags (core + approved community tags).
    In the future, this will query the database for community-approved tags.
    """
    # TODO: Add community tags from database
    return CORE_TAGS

def is_core_tag(tag: str) -> bool:
    """Check if a tag is a core predefined tag."""
    return tag.lower() in CORE_TAGS

def get_tag_description(tag: str) -> str:
    """Get description for a tag."""
    return TAG_DESCRIPTIONS.get(tag.lower(), f"Community tag: {tag}")

def validate_tags(tags: list) -> list:
    """Validate and clean a list of tags."""
    if not tags:
        return []
    
    # Clean and normalize tags
    cleaned_tags = []
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            cleaned_tag = tag.strip().lower().replace(' ', '-')
            if cleaned_tag not in cleaned_tags:  # Avoid duplicates
                cleaned_tags.append(cleaned_tag)
    
    return cleaned_tags[:5]  # Maximum 5 tags per tool

def build_ai_prompt_tags_section() -> str:
    """Build the tags section for AI prompts."""
    tags_list = "\n".join([f"- {tag}: {desc}" for tag, desc in TAG_DESCRIPTIONS.items()])
    
    return f"""
Available tags (choose 2-4 most relevant):
{tags_list}

Instructions:
- Select tags that best describe the tool's primary use case and target audience
- Prefer core functionality tags over secondary features
- Maximum 4 tags per tool
- Use exact tag names from the list above
"""
