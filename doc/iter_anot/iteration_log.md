# ANoT Iteration Log

## Round 1

### Issue
1. **Phase 1 Context Analysis returns empty** - LLM took 31s but returned nothing
2. **Phase 2 Script Generation returns empty** - Even with 30s processing time
3. **Script checks wrong conditions** - When script did generate, it checked wrong attributes

### Root Cause
1. Context analysis prompt was too verbose
2. Script generation prompt was too long and complex
3. No fallback when context analysis is empty

### Fix
1. Simplified CONTEXT_ANALYSIS_PROMPT with clear example
2. Simplified SCRIPT_GENERATION_PROMPT significantly
3. Added fallback: if context_analysis is empty, pass "(extract conditions from the user request)"
4. Added raw context to Phase 2 prompt so LLM has the user request

### Result
- Phase 1 now works! Returns proper CONDITIONS list
- Phase 2 now generates scripts (len=662)
- BUT: New issues emerged (see Round 2)

---

## Round 2

### Issue
1. **Wrong data paths in script** - Generated `{(input)}[NoiseLevel]` instead of `{(input)}[attributes][NoiseLevel]`
2. **Worker returns verbose text** - Instead of just 0/1/-1, returns "Please provide the statement..."
3. **Semantic interpretation wrong** - NoiseLevel='average' returned 0 instead of -1 (not quiet)
4. **Script invents non-existent keys** - `HOURS[OpenDuringWorkWindow]`, `REVIEWS`
5. **Missing data handling** - When HasTV doesn't exist, returns empty, then worker asks for clarification

### Root Cause
1. The example in SCRIPT_GENERATION_PROMPT showed `{(input)}[attributes][Key]` but wasn't strong enough
2. Worker prompt (via SYSTEM_PROMPT) doesn't enforce numeric-only output
3. The LLM doesn't understand 'average' noise means NOT quiet
4. LLM doesn't know the actual data schema

### Fix
(Next iteration)

### Result
[To be filled]
