# -*- coding: utf-8 -*-
"""
Bonus: Comparing 2 evaluation frameworks on the same dataset.

Here we compare the heuristic-based `RAGASEvaluator` with the prompt-based `LLMJudge`.
In production, you might compare `ragas` vs `deepeval`.
"""

from solution import QAPair, RAGASEvaluator, LLMJudge, BenchmarkRunner

def mock_llm_judge_api(prompt: str) -> str:
    """Mock LLM API that returns a JSON string of scores."""
    # A real implementation would call OpenAI or Anthropic here.
    return '{"faithfulness": 0.8, "relevance": 0.9, "completeness": 0.6}'

if __name__ == "__main__":
    qa_pairs = [
        QAPair(
            question="What is RAG?",
            expected_answer="RAG stands for Retrieval-Augmented Generation, which combines retrieval with text generation.",
            context="RAG is a technique that retrieves relevant documents and uses them to ground LLM generation.",
            metadata={"difficulty": "easy"}
        )
    ]

    def mock_agent(question: str) -> str:
        return f"RAG is Retrieval-Augmented Generation."

    print("=== Framework 1: RAGASEvaluator (Heuristics) ===")
    evaluator_1 = RAGASEvaluator()
    runner = BenchmarkRunner()
    results_1 = runner.run(qa_pairs, mock_agent, evaluator_1)
    
    for r in results_1:
        print(f"Question: {r.qa_pair.question}")
        print(f"  Faithfulness: {r.faithfulness:.2f}")
        print(f"  Relevance: {r.relevance:.2f}")
        print(f"  Completeness: {r.completeness:.2f}")

    print("\n=== Framework 2: LLMJudge (Prompt-based) ===")
    evaluator_2 = LLMJudge(judge_llm_fn=mock_llm_judge_api)
    
    rubric = {
        "faithfulness": "Is the answer grounded in the context?",
        "relevance": "Does it directly address the question?",
        "completeness": "Does it contain all expected information?"
    }
    
    for pair in qa_pairs:
        answer = mock_agent(pair.question)
        judge_result = evaluator_2.score_response(pair.question, answer, rubric)
        print(f"Question: {pair.question}")
        for criterion, score in judge_result["scores"].items():
            print(f"  {criterion.capitalize()}: {score:.2f}")
            
    print("\n=== Comparison ===")
    print("Heuristic methods (Framework 1) provide fast, deterministic word-overlap metrics.")
    print("LLM-as-Judge (Framework 2) is slower but can understand semantics and nuance better than simple overlap.")
