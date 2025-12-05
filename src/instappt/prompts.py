TRANSLATION_PROMPT = """You are a professional translator.
Translate the following text to {target_language} while maintaining perfection in these 5 dimensions:
1. **Accuracy:** Precise meaning preservation.
2. **Fluency:** Natural, native-level phrasing in {target_language}.
3. **Consistency:** Consistent terminology usage.
4. **Terminology:** Correct domain-specific vocabulary.
5. **Completeness:** No missing content.

IMPORTANT:
- If the source text is already in {target_language}, output it EXACTLY as is, preserving all case and formatting. Do not translate or modify it.
- Return ONLY the translated text.

Text:
{text}"""

EVALUATION_PROMPT = """
You are a professional linguistic evaluator.
Source Text: {source_text}
Target Language: {target_language}
Translation: {translation}

Evaluate the translation on:
1. Accuracy (1-10)
2. Fluency (1-10)
3. Consistency (1-10)
4. Terminology (1-10)
5. Completeness (1-10)

Provide specific suggestions for improvement if score < 10.
IMPORTANT: Please provide your suggestions in Chinese (简体中文).

Output JSON:
{{
  "metrics": {{
    "accuracy": int,
    "fluency": int,
    "consistency": int,
    "terminology": int,
    "completeness": int
  }},
  "suggestions": "string (in Chinese)",
  "overall_score": float
}}
"""

OPTIMIZATION_PROMPT = """You are a professional editor refining a translation.
Your goal is to optimize the translation to achieve perfection in the following 5 dimensions:
1. **Accuracy:** Precise meaning preservation.
2. **Fluency:** Natural, native-level phrasing in {target_language}.
3. **Consistency:** Consistent terminology usage.
4. **Terminology:** Correct domain-specific vocabulary.
5. **Completeness:** No missing content.

Target Language: {target_language}

Source Text:
{source_text}

Initial Translation:
{translation}

Evaluation Suggestions:
{suggestions}

Based on the Source Text and Suggestions, provide a refined translation that maximizes quality across these 5 dimensions.
Return ONLY the optimized translated text."""
