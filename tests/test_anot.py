#!/usr/bin/env python3
"""Unit tests for ANoT parsing and substitution logic.

These tests ensure fast iteration during development by catching
parsing/substitution bugs without running full LLM requests.
"""

import pytest
from utils.parsing import substitute_variables, parse_script, parse_indices
from methods.anot.helpers import (
    extract_dependencies, build_execution_layers,
    parse_conditions, parse_resolved_path, parse_candidates, parse_lwt_skeleton
)


# =============================================================================
# SUBSTITUTE_VARIABLES TESTS
# =============================================================================

class TestSubstituteVariables:
    """Tests for variable substitution in LWT templates."""

    @pytest.fixture
    def sample_items(self):
        """Sample restaurant data matching actual dataset structure."""
        return {
            "1": {
                "name": "Milkcrate Cafe",
                "attributes": {
                    "WiFi": "u'free'",
                    "GoodForKids": "True",
                    "DriveThru": "True",
                    "CoatCheck": "False",
                    "BikeParking": "True",
                    "NoiseLevel": "u'average'",
                },
                "hours": {
                    "Monday": "8:0-15:0",
                    "Tuesday": "8:0-15:0",
                },
                "reviews": [
                    {"text": "Great coffee!", "stars": 5},
                    {"text": "Nice atmosphere", "stars": 4},
                ]
            },
            "7": {
                "name": "Tria Cafe",
                "attributes": {
                    "WiFi": "u'no'",
                    "GoodForKids": "False",
                    "CoatCheck": None,
                    "BikeParking": "True",
                },
                "reviews": [
                    {"text": "Good wine selection", "stars": 4},
                ]
            }
        }

    def test_simple_context_access(self, sample_items):
        """Test basic context variable access."""
        template = "{(context)}[1][name]"
        result = substitute_variables(template, sample_items, "", {})
        assert result == "Milkcrate Cafe"

    def test_nested_attribute_access(self, sample_items):
        """Test nested attribute access - the common failure case."""
        template = "{(context)}[1][attributes][WiFi]"
        result = substitute_variables(template, sample_items, "", {})
        assert result == "u'free'", f"Got: '{result}'"

    def test_multiple_attributes_in_template(self, sample_items):
        """Test template with multiple attribute substitutions."""
        template = "WiFi={(context)}[1][attributes][WiFi], Kids={(context)}[1][attributes][GoodForKids]"
        result = substitute_variables(template, sample_items, "", {})
        assert "WiFi=u'free'" in result
        assert "Kids=True" in result

    def test_different_item_indices(self, sample_items):
        """Test accessing different items by index."""
        template1 = "{(context)}[1][name]"
        template7 = "{(context)}[7][name]"

        result1 = substitute_variables(template1, sample_items, "", {})
        result7 = substitute_variables(template7, sample_items, "", {})

        assert result1 == "Milkcrate Cafe"
        assert result7 == "Tria Cafe"

    def test_none_attribute_value(self, sample_items):
        """Test handling of None values in attributes."""
        template = "{(context)}[7][attributes][CoatCheck]"
        result = substitute_variables(template, sample_items, "", {})
        # None should become "None" string
        assert result == "None", f"Got: '{result}'"

    def test_missing_attribute(self, sample_items):
        """Test accessing non-existent attribute."""
        template = "{(context)}[1][attributes][NonExistent]"
        result = substitute_variables(template, sample_items, "", {})
        # Should return empty string for missing keys
        assert result == "", f"Got: '{result}'"

    def test_missing_item_index(self, sample_items):
        """Test accessing non-existent item index."""
        template = "{(context)}[99][name]"
        result = substitute_variables(template, sample_items, "", {})
        assert result == "", f"Got: '{result}'"

    def test_review_access(self, sample_items):
        """Test accessing review data."""
        template = "{(context)}[1][reviews][0][text]"
        result = substitute_variables(template, sample_items, "", {})
        assert result == "Great coffee!"

    def test_hours_access(self, sample_items):
        """Test accessing hours data."""
        template = "{(context)}[1][hours][Monday]"
        result = substitute_variables(template, sample_items, "", {})
        assert result == "8:0-15:0"

    def test_query_substitution(self, sample_items):
        """Test {(query)} substitution."""
        template = "User wants: {(query)}"
        result = substitute_variables(template, sample_items, "quiet cafe with WiFi", {})
        assert result == "User wants: quiet cafe with WiFi"

    def test_cache_substitution(self, sample_items):
        """Test substitution from cache (previous step results)."""
        cache = {"c1": "yes", "c2": "no", "final": "[1, 7]"}
        template = "c1={(c1)}, c2={(c2)}"
        result = substitute_variables(template, sample_items, "", cache)
        assert result == "c1=yes, c2=no"

    def test_mixed_substitution(self, sample_items):
        """Test template with context, query, and cache."""
        cache = {"c1": "yes"}
        template = "Query: {(query)}, Item1 WiFi: {(context)}[1][attributes][WiFi], c1={(c1)}"
        result = substitute_variables(template, sample_items, "test query", cache)
        assert "Query: test query" in result
        assert "Item1 WiFi: u'free'" in result
        assert "c1=yes" in result

    def test_integer_key_fallback(self):
        """Test that integer keys work when dict has int keys."""
        items = {
            1: {"name": "Test"},  # int key, not string
            "2": {"name": "Test2"},  # string key
        }
        # Both should work
        result1 = substitute_variables("{(context)}[1][name]", items, "", {})
        result2 = substitute_variables("{(context)}[2][name]", items, "", {})
        assert result1 == "Test", f"Int key failed: '{result1}'"
        assert result2 == "Test2", f"String key failed: '{result2}'"

    def test_no_unresolved_variables(self, sample_items):
        """Ensure no {( patterns remain after substitution."""
        template = "{(context)}[1][name] and {(query)}"
        result = substitute_variables(template, sample_items, "test", {})
        assert "{(" not in result, f"Unresolved variable in: {result}"

    def test_complex_prompt_template(self, sample_items):
        """Test a realistic LWT prompt template."""
        template = (
            "Item 1: WiFi={(context)}[1][attributes][WiFi], "
            "DriveThru={(context)}[1][attributes][DriveThru], "
            "GoodForKids={(context)}[1][attributes][GoodForKids]. "
            "Does item 1 satisfy: {(query)}? Answer yes/no."
        )
        result = substitute_variables(template, sample_items, "cafe with WiFi", {})

        assert "WiFi=u'free'" in result
        assert "DriveThru=True" in result
        assert "GoodForKids=True" in result
        assert "cafe with WiFi" in result
        assert "{(" not in result


# =============================================================================
# PARSE_SCRIPT TESTS
# =============================================================================

class TestParseScript:
    """Tests for LWT script parsing."""

    def test_simple_script(self):
        """Test parsing a simple LWT script."""
        script = """
        (c1)=LLM("Check item 1")
        (c2)=LLM("Check item 2")
        (final)=LLM("Aggregate results")
        """
        steps = parse_script(script)
        assert len(steps) == 3
        assert steps[0] == ("c1", "Check item 1")
        assert steps[1] == ("c2", "Check item 2")
        assert steps[2] == ("final", "Aggregate results")

    def test_single_quotes(self):
        """Test parsing with single quotes."""
        script = "(c1)=LLM('Check item 1')"
        steps = parse_script(script)
        assert len(steps) == 1
        assert steps[0] == ("c1", "Check item 1")

    def test_hierarchical_ids(self):
        """Test parsing hierarchical step IDs like (2.rev.0)."""
        script = """
        (2.rev.0)=LLM("Check review 0 of item 2")
        (2.rev.1)=LLM("Check review 1 of item 2")
        """
        steps = parse_script(script)
        assert len(steps) == 2
        assert steps[0][0] == "2.rev.0"
        assert steps[1][0] == "2.rev.1"

    def test_spaces_around_equals(self):
        """Test parsing with spaces around = sign."""
        script = "(c1) = LLM(\"Check item\")"
        steps = parse_script(script)
        assert len(steps) == 1
        assert steps[0] == ("c1", "Check item")

    def test_skips_non_llm_lines(self):
        """Test that non-LLM lines are skipped."""
        script = """
        # This is a comment
        (c1)=LLM("Check item 1")
        Some other text
        (c2)=LLM("Check item 2")
        """
        steps = parse_script(script)
        assert len(steps) == 2

    def test_template_with_variables(self):
        """Test parsing templates that contain variable patterns."""
        script = '(c1)=LLM("WiFi={{{(context)}}[1][attributes][WiFi]}. Has free WiFi?")'
        steps = parse_script(script)
        # Should preserve the variable pattern
        assert len(steps) == 1
        assert "{(context)}" in steps[0][1] or "context" in steps[0][1]


# =============================================================================
# DEPENDENCY EXTRACTION TESTS
# =============================================================================

class TestExtractDependencies:
    """Tests for dependency extraction from LWT instructions."""

    def test_no_dependencies(self):
        """Test instruction with no dependencies."""
        instr = "Check item {(context)}[1][name]"
        deps = extract_dependencies(instr)
        # context is a reserved input, not a step dependency
        assert "context" in deps or len(deps) == 1

    def test_single_dependency(self):
        """Test instruction with one step dependency."""
        instr = "Based on {(c1)}, make decision"
        deps = extract_dependencies(instr)
        assert "c1" in deps

    def test_multiple_dependencies(self):
        """Test instruction with multiple dependencies."""
        instr = "c1={(c1)}, c2={(c2)}, c3={(c3)}. Aggregate."
        deps = extract_dependencies(instr)
        assert deps == {"c1", "c2", "c3"}

    def test_hierarchical_dependency(self):
        """Test extraction of hierarchical step IDs."""
        instr = "Result from {(2.rev.0)} and {(2.rev.1)}"
        deps = extract_dependencies(instr)
        assert "2.rev.0" in deps
        assert "2.rev.1" in deps


# =============================================================================
# BUILD_EXECUTION_LAYERS TESTS
# =============================================================================

class TestBuildExecutionLayers:
    """Tests for DAG layer building."""

    def test_independent_steps(self):
        """Test steps with no interdependencies."""
        steps = [
            ("c1", "Check {(context)}[1]"),
            ("c2", "Check {(context)}[2]"),
            ("c3", "Check {(context)}[3]"),
        ]
        layers = build_execution_layers(steps)
        # All should be in same layer (parallel)
        assert len(layers) == 1
        assert len(layers[0]) == 3

    def test_sequential_dependencies(self):
        """Test steps that must run sequentially."""
        steps = [
            ("c1", "Check {(context)}[1]"),
            ("c2", "Based on {(c1)}, check more"),
            ("final", "Based on {(c2)}, decide"),
        ]
        layers = build_execution_layers(steps)
        # Each step depends on previous, so 3 layers
        assert len(layers) == 3

    def test_mixed_dependencies(self):
        """Test mix of parallel and sequential steps."""
        steps = [
            ("c1", "Check {(context)}[1]"),
            ("c2", "Check {(context)}[2]"),
            ("c3", "Check {(context)}[3]"),
            ("final", "Aggregate {(c1)}, {(c2)}, {(c3)}"),
        ]
        layers = build_execution_layers(steps)
        # c1, c2, c3 parallel in layer 0; final in layer 1
        assert len(layers) == 2
        assert len(layers[0]) == 3
        assert len(layers[1]) == 1

    def test_cycle_detection(self):
        """Test that cycles raise an error."""
        steps = [
            ("a", "Depends on {(b)}"),
            ("b", "Depends on {(a)}"),
        ]
        with pytest.raises(ValueError, match="Cycle"):
            build_execution_layers(steps)

    def test_empty_steps(self):
        """Test empty step list."""
        layers = build_execution_layers([])
        assert layers == []


# =============================================================================
# PARSE_INDICES TESTS
# =============================================================================

class TestParseIndices:
    """Tests for parsing ranking output."""

    def test_comma_separated(self):
        """Test parsing comma-separated indices."""
        response = "3, 1, 5, 7"
        indices = parse_indices(response, max_index=10, k=5)
        assert indices == [3, 1, 5, 7]

    def test_space_separated(self):
        """Test parsing space-separated indices."""
        response = "3 1 5 7"
        indices = parse_indices(response, max_index=10, k=5)
        assert indices == [3, 1, 5, 7]

    def test_with_text(self):
        """Test parsing indices mixed with text."""
        response = "The best items are 3, 1, and 5."
        indices = parse_indices(response, max_index=10, k=5)
        assert 3 in indices
        assert 1 in indices
        assert 5 in indices

    def test_respects_max_index(self):
        """Test that indices beyond max_index are ignored."""
        response = "1, 5, 99, 3"
        indices = parse_indices(response, max_index=10, k=5)
        assert 99 not in indices
        assert indices == [1, 5, 3]

    def test_respects_k_limit(self):
        """Test that only k indices are returned."""
        response = "1, 2, 3, 4, 5, 6, 7"
        indices = parse_indices(response, max_index=10, k=3)
        assert len(indices) == 3

    def test_deduplication(self):
        """Test that duplicate indices are removed."""
        response = "1, 1, 2, 2, 3"
        indices = parse_indices(response, max_index=10, k=5)
        assert indices == [1, 2, 3]


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
