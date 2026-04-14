

# LEAN Philosophy

_Stay informed without getting engaged._

LEAN — Low Engagement AI News — is a news feed produced by AI, built to summarize the news while removing emotional engagement and clutter. By doing so, it allows the reader to feel a sense of clarity without risking the doom-scrolling cycle.

***

### The Engagement Economy

The concept of the attention economy was first articulated by Nobel Laureate Herbert Simon in 1971, who observed that a wealth of information creates a poverty of attention — what was then a theoretical insight has since become a deliberate business model. Platforms offer "free" services but generate revenue by selling targeted advertising, with algorithms feeding users whatever content maximizes time spent and clicks. As researchers have noted, the most effective content for this purpose tends to be sensational, divisive, or outrage-inducing, because emotional responses are what keep us clicking and sharing.

This is rarely in the news reader's interest. A 2022 study in _Health Communication_ found that 16.5% of adults surveyed showed signs of "severely problematic" news consumption, with stories dominating their waking thoughts and contributing to an inability to sleep. LEAN is built as a quiet rebellion against this — a feed you read until it ends, without being provoked or artificially reassured.

***

### No Replacement for Real Journalism

At a time when people speculate that AI can replace human labor, I want to be clear: this tool is not designed to do that. Real journalism is complex, professional, and often dangerous work. I do not believe AI can replace it.

What this tool does is narrower: it takes articles from RSS feeds created by professional journalists, summarizes them, and removes emotional tone. The reporting remains entirely human. The AI only shapes the delivery.

***

### On Bias, Responsibility, and Limits

The feed is generated automatically by AI. I do not manually select, edit, or prioritize individual stories. This means:

* I do not inject my personal opinions
* I do not decide what the reader _should_ know
* I do not shape the narrative beyond defining the system itself

Content is pulled from multiple RSS sources to reduce dependence on any single editorial line. The system then filters and summarizes based on predefined rules.

However, **this does not mean the system is neutral**. Bias can still enter through source selection, model behavior (the system currently uses Anthropic models), and summarization constraints.

The reader should be aware that AI can make mistakes. I am only responsible for designing the system to reduce errors as well as I can — but I am not responsible for any specific piece of content it produces. I trust the reader to understand the limitations of this system.

***

### Design

LEAN is designed to mimic the experience of reading a print newspaper: you receive one edition in the morning, it contains a fixed amount of information, you read it, and then there is nothing left to read. No refreshing. No autoplay. No emotional bait.

An AI agent aggregates, filters, and rewrites — stripping agitation from the signal.

**The pipeline:**

1. Pull articles from RSS feeds
2. Deduplicate by repeated keywords
3. Filter by relevance and significance
4. Summarize into a structured, calm HTML digest
5. Deliver by email, twice a day

The editorial rules enforced on the output — no ALL CAPS, no sensationalism, no exclamation marks — are not stylistic preferences. They are the whole point.

***

### The Role of Mantras

I consider reading the news a serious task — one that can bring difficult feelings even when the language is calm. Modern neuroscience supports what contemplative traditions have long known: the repetition of a mantra helps quiet the mind by redirecting attention, promoting mental clarity and reducing mental chatter. At a neurological level, repetitive speech produces a global reduction in brain activity, suppressing the default mode network responsible for mind-wandering — which may account for the uniquely calming effect of mantra practice.

By including a mantra at the beginning and end of each feed, the reader is invited to start with a calm, stoic eye — and when finished, to close the digest and move on with their day.

***

### Working Principles

* **Finite by default** — one digest you can finish, then leave
* **Signal over noise** — repeated stories are merged, not amplified
* **Context over urgency** — relevance and significance matter more than novelty
* **Calm language** — writing should inform, not provoke
* **Source plurality** — multiple perspectives, without endless scrolling




