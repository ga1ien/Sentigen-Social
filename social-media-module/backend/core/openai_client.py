"""
OpenAI client utilities

Includes:
- GPT5MiniClient: helpers tailored for gpt-5-mini normalization flows
- OpenAIClient: generic wrapper exposing generate_completion used by APIs
"""

import json
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI


class GPT5MiniClient:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.model = "gpt-5-mini"

    def normalize_chat_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameters for GPT-5 Mini compatibility"""
        p = params.copy()

        # GPT-5 Mini doesn't allow custom samplers
        if "temperature" in p:
            del p["temperature"]
        if "top_p" in p:
            del p["top_p"]
        if "frequency_penalty" in p:
            del p["frequency_penalty"]
        if "presence_penalty" in p:
            del p["presence_penalty"]

        # Token field naming for GPT-5
        if "max_tokens" in p and "max_completion_tokens" not in p:
            p["max_completion_tokens"] = p["max_tokens"]
            del p["max_tokens"]

        return p

    async def extract_content(self, raw_content: str, platform: str) -> List[Dict[str, Any]]:
        """Extract structured content using GPT-5 Mini"""

        extraction_prompts = {
            "linkedin": """
Output STRICT JSON:
{"items":[{"title":"","author":"","company":"","content":"","engagement":{"likes":0,"comments":0,"shares":0},"url":"","timestamp":"","post_type":"text|image|video|article","industry_tags":[],"ai_relevance_score":0.0}]}

Rules:
- Extract ALL LinkedIn posts from the input
- Focus on AI, content creation, and advertising topics
- Normalize engagement numbers (convert "1K" to 1000)
- Rate AI relevance 0.0-1.0
- Return only valid JSON
            """,
            "substack": """
Output STRICT JSON:
{"items":[{"title":"","author":"","publication":"","excerpt":"","content":"","url":"","published_date":"","subscriber_count":null,"read_time":"","tags":[],"ai_relevance_score":0.0,"quality_score":0.0}]}

Rules:
- Extract ALL Substack articles from the input
- Focus on AI, content creation, and future of media
- Extract full article content when available
- Rate AI relevance and quality 0.0-1.0
- Return only valid JSON
            """,
            "reddit": """
Output STRICT JSON:
{"items":[{"title":"","author":"","subreddit":"","content":"","url":"","score":0,"comments_count":0,"created_utc":"","post_type":"text|link|image|video","comments":[{"author":"","content":"","score":0,"created_utc":""}],"ai_relevance_score":0.0}]}

Rules:
- Extract ALL Reddit posts and top comments from the input
- Focus on AI, content creation, and advertising discussions
- Include comment threads for context
- Rate AI relevance 0.0-1.0
- Return only valid JSON
            """,
        }

        prompt = extraction_prompts.get(platform, extraction_prompts["linkedin"])

        try:
            response = await self.client.chat.completions.create(
                **self.normalize_chat_params(
                    {
                        "model": self.model,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": raw_content}],
                        "max_completion_tokens": 8000,
                    }
                )
            )

            result = json.loads(response.choices[0].message.content or '{"items":[]}')
            return result.get("items", [])

        except Exception as e:
            print(f"❌ GPT-5 Mini extraction failed: {e}")
            return []

    async def normalize_content(self, raw_items: List[Dict], platform: str) -> List[Dict[str, Any]]:
        """Normalize and clean extracted content using GPT-5 Mini"""

        normalization_prompt = f"""
You are a {platform} content normalization expert. Clean and standardize this data:

CRITICAL RULES:
- Remove duplicate or very similar items
- Standardize timestamps to ISO format
- Clean "null" strings to actual null values
- Normalize engagement metrics consistently
- Extract key themes and topics
- Rate content quality and AI relevance
- Merge similar posts from same author
- Fix formatting and encoding issues

Return the same JSON structure but cleaned and normalized.
        """

        try:
            response = await self.client.chat.completions.create(
                **self.normalize_chat_params(
                    {
                        "model": self.model,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": normalization_prompt},
                            {"role": "user", "content": json.dumps({"items": raw_items})},
                        ],
                        "max_completion_tokens": 8000,
                    }
                )
            )

            result = json.loads(response.choices[0].message.content or '{"items":[]}')
            return result.get("items", [])

        except Exception as e:
            print(f"❌ GPT-5 Mini normalization failed: {e}")
            return raw_items

    async def analyze_insights(self, normalized_items: List[Dict], platform: str, search_query: str) -> Dict[str, Any]:
        """Generate comprehensive insights using GPT-5 Mini"""

        analysis_prompt = f"""
Analyze this {platform} content about "{search_query}" and provide comprehensive insights:

ANALYSIS REQUIREMENTS:
1. Key themes and trends
2. Top authors/influencers
3. Engagement patterns
4. Content quality assessment
5. AI relevance and applications
6. Actionable insights for content creators
7. Market opportunities identified
8. Sentiment analysis
9. Competitive landscape
10. Future predictions

Return detailed JSON analysis with specific examples and data points.
        """

        try:
            response = await self.client.chat.completions.create(
                **self.normalize_chat_params(
                    {
                        "model": self.model,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": analysis_prompt},
                            {
                                "role": "user",
                                "content": json.dumps(
                                    {
                                        "platform": platform,
                                        "search_query": search_query,
                                        "items": normalized_items,
                                        "total_items": len(normalized_items),
                                    }
                                ),
                            },
                        ],
                        "max_completion_tokens": 4000,
                    }
                )
            )

            return json.loads(response.choices[0].message.content or "{}")

        except Exception as e:
            print(f"❌ GPT-5 Mini analysis failed: {e}")
            return {"error": str(e), "platform": platform, "items_analyzed": len(normalized_items)}

    async def create_search_strategy(self, query: str, platform: str) -> Dict[str, Any]:
        """Create intelligent search strategy using GPT-5 Mini"""

        strategy_prompt = f"""
Create an intelligent search strategy for {platform} to find content about "{query}".

STRATEGY REQUIREMENTS:
1. Primary search terms (3-5 variations)
2. Secondary keywords to try
3. Platform-specific search tactics
4. Quality indicators to look for
5. Content filters and preferences
6. Engagement thresholds
7. Author/source preferences
8. Time-based considerations

Return JSON strategy with specific, actionable search parameters.
        """

        try:
            response = await self.client.chat.completions.create(
                **self.normalize_chat_params(
                    {
                        "model": self.model,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": strategy_prompt},
                            {"role": "user", "content": f"Query: {query}, Platform: {platform}"},
                        ],
                        "max_completion_tokens": 2000,
                    }
                )
            )

            return json.loads(response.choices[0].message.content or "{}")

        except Exception as e:
            print(f"❌ GPT-5 Mini strategy creation failed: {e}")
            return {
                "primary_search_terms": [query],
                "quality_indicators": ["high engagement", "recent posts", "detailed content"],
                "platform_tactics": [f"standard {platform} search"],
            }


class OpenAIClient:
    """
    Backwards-compatible wrapper used by some API modules.

    Provides a simple generate_completion(prompt, ...) that returns string content.
    Model can be set via LLM_CHOICE env; defaults to gpt-4o-mini. Uses the same
    normalization approach as GPT5MiniClient for compatibility with gpt-5-* models.
    """

    def __init__(self, model: Optional[str] = None):
        self.client = AsyncOpenAI()
        self.model = model or os.getenv("LLM_CHOICE", "gpt-4o-mini")
        # Reuse normalization behavior to support gpt-5 parameter schema if selected
        self._normalizer = GPT5MiniClient().normalize_chat_params

    async def generate_completion(self, *, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        try:
            params: Dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                # Prefer the older name; the normalizer will translate when needed
                "max_tokens": max_tokens,
                # Temperature is removed for gpt-5-mini by normalizer
                "temperature": temperature,
            }

            resp = await self.client.chat.completions.create(**self._normalizer(params))
            return resp.choices[0].message.content or ""
        except Exception as e:
            # Fail soft with empty string; callers often have fallbacks
            print(f"❌ OpenAIClient.generate_completion failed: {e}")
            return ""
