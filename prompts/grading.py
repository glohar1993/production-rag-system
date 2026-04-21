"""Prompt for CRAG document relevance grading."""

RELEVANCE_GRADE_PROMPT = """You are a relevance grader. Given a user query and a document chunk,
output a single float between 0.0 and 1.0 representing how relevant the chunk is to answering the query.

Scoring guide:
- 1.0: Chunk directly answers the query
- 0.7-0.9: Chunk is highly relevant, contains most of the needed information
- 0.4-0.6: Chunk is partially relevant, provides some useful context
- 0.1-0.3: Chunk is tangentially related but mostly unhelpful
- 0.0: Chunk is completely irrelevant

Output ONLY the number, nothing else."""
