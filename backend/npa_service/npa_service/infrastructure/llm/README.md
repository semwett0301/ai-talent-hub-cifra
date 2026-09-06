# llm

`OpenRouterChangeSummarizer` sends a bounded unified diff to the configured DeepSeek
model twice: once for concise per-article changes and once for a detailed overall summary.
Both calls validate structured output, have independent output-token limits, and set
OpenRouter reasoning to disabled. No call is made when the stage changes but the selected
text is byte-for-byte unchanged.
