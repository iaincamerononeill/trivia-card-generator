"""
AI Question Generator
Generates trivia questions using various AI APIs (OpenAI, Anthropic, Google)
"""

import json
from typing import List, Dict


def generate_questions(topic: str, level: str, num_cards: int, api_provider: str, api_key: str) -> str:
    """
    Generate trivia questions using AI
    
    Args:
        topic: The topic for questions (e.g., "Ancient Rome", "Space", "Biology")
        level: Difficulty level (e.g., "Primary School", "Secondary School", "Adult")
        num_cards: Number of cards to generate (each card has 6 questions)
        api_provider: 'openai', 'anthropic', or 'google'
        api_key: API key for the provider
    
    Returns:
        CSV formatted string with generated questions
    """
    if api_provider == 'openai':
        return generate_with_openai(topic, level, num_cards, api_key)
    elif api_provider == 'anthropic':
        return generate_with_anthropic(topic, level, num_cards, api_key)
    elif api_provider == 'google':
        return generate_with_google(topic, level, num_cards, api_key)
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")


def generate_with_openai(topic: str, level: str, num_cards: int, api_key: str) -> str:
    """Generate questions using OpenAI API"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Please install openai: pip install openai")
    
    client = OpenAI(api_key=api_key)
    
    total_questions = num_cards * 6
    
    prompt = f"""Generate {total_questions} trivia questions about "{topic}" suitable for "{level}" level.

Requirements:
- Provide exactly {total_questions} questions
- Questions must be varied across 6 subjects/categories
- Each set of 6 questions should cover different aspects
- Questions should be appropriate for {level} difficulty
- Answers should be concise (1-3 words or short phrase)

Format as CSV with columns: level,subject,question,answer
Use these subject codes cycling through them: M,S,E,H,G,C

Example:
{level},M,What is 5 x 7?,35
{level},S,What planet is closest to the Sun?,Mercury

Generate {total_questions} questions now:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a trivia question generator. Output only CSV format with no additional text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    
    csv_content = response.choices[0].message.content.strip()
    
    # Add header if not present
    if not csv_content.startswith('level,'):
        csv_content = 'level,subject,question,answer\n' + csv_content
    
    return csv_content


def generate_with_anthropic(topic: str, level: str, num_cards: int, api_key: str) -> str:
    """Generate questions using Anthropic Claude API"""
    try:
        import anthropic
    except ImportError:
        raise ImportError("Please install anthropic: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    total_questions = num_cards * 6
    
    prompt = f"""Generate {total_questions} trivia questions about "{topic}" suitable for "{level}" level.

Requirements:
- Provide exactly {total_questions} questions
- Questions must be varied across 6 subjects/categories
- Each set of 6 questions should cover different aspects
- Questions should be appropriate for {level} difficulty
- Answers should be concise (1-3 words or short phrase)

Format as CSV with header: level,subject,question,answer
Use these subject codes cycling through them: M,S,E,H,G,C

Generate {total_questions} questions now in CSV format only:"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    csv_content = message.content[0].text.strip()
    
    # Add header if not present
    if not csv_content.startswith('level,'):
        csv_content = 'level,subject,question,answer\n' + csv_content
    
    return csv_content


def generate_with_google(topic: str, level: str, num_cards: int, api_key: str) -> str:
    """Generate questions using Google Gemini API"""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Please install google-generativeai: pip install google-generativeai")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    total_questions = num_cards * 6
    
    prompt = f"""Generate {total_questions} trivia questions about "{topic}" suitable for "{level}" level.

Requirements:
- Provide exactly {total_questions} questions
- Questions must be varied across 6 subjects/categories
- Each set of 6 questions should cover different aspects
- Questions should be appropriate for {level} difficulty
- Answers should be concise (1-3 words or short phrase)

Format as CSV with header: level,subject,question,answer
Use these subject codes cycling through them: M,S,E,H,G,C

Generate {total_questions} questions now in CSV format only:"""

    response = model.generate_content(prompt)
    csv_content = response.text.strip()
    
    # Add header if not present
    if not csv_content.startswith('level,'):
        csv_content = 'level,subject,question,answer\n' + csv_content
    
    return csv_content
