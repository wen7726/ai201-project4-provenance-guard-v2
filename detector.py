import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def clamp(value, min_value=0.0, max_value=1.0):
    return max(min_value, min(value, max_value))


def llm_detection_score(text):
    prompt = f"""
Analyze whether this text appears AI-generated or human-written.

Return ONLY valid JSON:
{{
  "score": 0.5,
  "reason": "brief explanation"
}}

Score meaning:
0.0 = very likely human-written
0.5 = uncertain
1.0 = very likely AI-generated

Text:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)

        return {
            "score": clamp(float(data.get("score", 0.5))),
            "reason": data.get("reason", "No reason provided.")
        }

    except Exception as e:
        return {
            "score": 0.5,
            "reason": f"LLM signal unavailable or uncertain: {str(e)}"
        }


def split_sentences(text):
    sentences = re.split(r"[.!?]+", text)
    return [s.strip() for s in sentences if s.strip()]


def stylometric_score(text):
    words = re.findall(r"\b\w+\b", text.lower())
    sentences = split_sentences(text)

    if len(words) < 20 or len(sentences) == 0:
        return {
            "score": 0.5,
            "metrics": {
                "reason": "Text too short for stable stylometric analysis."
            }
        }

    word_count = len(words)
    unique_words = len(set(words))
    type_token_ratio = unique_words / word_count

    sentence_lengths = [
        len(re.findall(r"\b\w+\b", sentence.lower()))
        for sentence in sentences
    ]

    avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)

    if len(sentence_lengths) > 1:
        mean = avg_sentence_length
        variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    else:
        variance = 0

    punctuation_count = len(re.findall(r"[,.!?;:]", text))
    punctuation_density = punctuation_count / word_count

    score = 0.0

    if type_token_ratio > 0.55:
        score += 0.25

    if variance < 20:
        score += 0.30
    elif variance < 40:
        score += 0.15

    if avg_sentence_length > 18:
        score += 0.25
    elif avg_sentence_length > 14:
        score += 0.15

    if 0.04 <= punctuation_density <= 0.12:
        score += 0.20

    return {
        "score": clamp(score),
        "metrics": {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "type_token_ratio": round(type_token_ratio, 3),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "sentence_length_variance": round(variance, 2),
            "punctuation_density": round(punctuation_density, 3),
        }
    }


def combine_scores(llm_score, style_score):
    return round(clamp((llm_score * 0.65) + (style_score * 0.35)), 3)


def attribution_from_score(score):
    if score >= 0.70:
        return "likely_ai"
    if score <= 0.30:
        return "likely_human"
    return "uncertain"


def transparency_label(attribution):
    labels = {
        "likely_ai": "This content shows strong signs of being AI-generated. This label is based on multiple detection signals and should be treated as a transparency notice, not a final judgment.",
        "likely_human": "This content shows strong signs of being human-written. The system found low evidence of AI generation, but no automated review can guarantee authorship.",
        "uncertain": "The system could not confidently determine whether this content was human-written or AI-generated. Readers should treat the attribution as uncertain, and the creator may provide additional context."
    }
    return labels[attribution]
