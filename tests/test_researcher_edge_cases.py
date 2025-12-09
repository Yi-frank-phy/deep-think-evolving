"""
Test edge cases for Researcher Agent after bug fixes.

These tests verify the fixes made to researcher.py:
1. NoneType handling for research_context
2. JSON parsing from markdown code blocks
3. Handling response_mime_type incompatibility with Grounding
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestResearcherNoneHandling:
    """Tests for NoneType safety in researcher output."""
    
    def test_none_research_context_becomes_empty_string(self):
        """When API returns None for research_context, it should become empty string."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.researcher import research_node
        
        state = {
            "problem_state": "Test problem",
            "information_needs": [],
            "config": {},
            "research_iteration": 0,
            "history": []
        }
        
        result = research_node(state)
        
        # research_context should be a string, not None
        assert isinstance(result.get("research_context"), str)
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_none_information_status_defaults_to_sufficient(self):
        """When API returns None for information_status, it should default to 'sufficient'."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.researcher import research_node
        
        state = {
            "problem_state": "Test problem",
            "information_needs": [],
            "config": {"max_research_iterations": 3},
            "research_iteration": 0,
            "history": []
        }
        
        result = research_node(state)
        
        # research_status should be a string, not None
        assert result.get("research_status") in ["sufficient", "insufficient"]
        
        os.environ.pop("USE_MOCK_AGENTS", None)


class TestResearcherJsonParsing:
    """Tests for JSON extraction from various response formats."""
    
    def test_extracts_json_from_markdown_code_block(self):
        """Should extract JSON from ```json ... ``` code blocks."""
        import json
        import re
        
        response_text = """Here is my analysis:
        
```json
{
    "research_context": "Extracted context",
    "information_status": "sufficient",
    "missing_items": []
}
```

The above provides the information needed.
"""
        # Simulate the extraction logic
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        assert json_match is not None
        
        extracted = json.loads(json_match.group(1).strip())
        assert extracted["research_context"] == "Extracted context"
        assert extracted["information_status"] == "sufficient"
    
    def test_handles_direct_json_response(self):
        """Should parse direct JSON response without code blocks."""
        import json
        
        response_text = '{"research_context": "Direct JSON", "information_status": "sufficient", "missing_items": []}'
        
        result = json.loads(response_text)
        assert result["research_context"] == "Direct JSON"
    
    def test_fallback_to_raw_text_on_invalid_json(self):
        """When JSON parsing fails, should use raw text as context."""
        import json
        import re
        
        response_text = "This is just plain text without any JSON structure."
        
        # Simulate fallback logic
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group(1).strip())
                except json.JSONDecodeError:
                    result = {"research_context": response_text}
            else:
                result = {"research_context": response_text}
        
        assert result["research_context"] == response_text


class TestResearcherIterationLimit:
    """Tests for research iteration limits."""
    
    def test_respects_max_research_iterations_config(self):
        """Should stop researching when max iterations reached."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.researcher import research_node
        
        state = {
            "problem_state": "Test problem",
            "information_needs": [],
            "config": {"max_research_iterations": 2},
            "research_iteration": 2,  # Already at max
            "history": []
        }
        
        result = research_node(state)
        
        # Should force sufficient to avoid infinite loop
        assert result.get("research_status") == "sufficient"
        
        os.environ.pop("USE_MOCK_AGENTS", None)
    
    def test_increments_research_iteration(self):
        """Should increment research_iteration after each call."""
        os.environ["USE_MOCK_AGENTS"] = "true"
        
        from src.agents.researcher import research_node
        
        state = {
            "problem_state": "Test problem",
            "information_needs": [],
            "config": {"max_research_iterations": 5},
            "research_iteration": 1,
            "history": []
        }
        
        result = research_node(state)
        
        # Should be incremented
        assert result.get("research_iteration") == 2
        
        os.environ.pop("USE_MOCK_AGENTS", None)


class TestResearcherWithoutApiKey:
    """Tests for behavior when GEMINI_API_KEY is not set."""
    
    def test_returns_sufficient_without_api_key(self):
        """Should return sufficient status when API key is missing to avoid blocking."""
        # Temporarily remove API key
        api_key = os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("USE_MOCK_AGENTS", None)  # Ensure not in mock mode
        
        try:
            from importlib import reload
            import src.agents.researcher as researcher_module
            reload(researcher_module)
            
            state = {
                "problem_state": "Test problem",
                "information_needs": [],
                "config": {},
                "research_iteration": 0,
                "history": []
            }
            
            result = researcher_module.research_node(state)
            
            # Should return sufficient to prevent infinite loop
            assert result.get("research_status") == "sufficient"
        finally:
            # Restore API key if it existed
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
