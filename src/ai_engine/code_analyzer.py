"""
AI-powered code complexity analyzer using GPT-4.
"""
import openai
from typing import Dict, List, Optional
from dataclasses import dataclass
import ast
import re


@dataclass
class ComplexityScore:
    score: float  # 0-10 scale
    metrics: Dict[str, float]
    suggestions: List[str]
    suitable_for_beginner: bool


class CodeAnalyzer:
    """Analyzes code complexity using AI and static analysis."""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def analyze_file(self, file_path: str) -> ComplexityScore:
        """Analyze a single file for complexity."""
        with open(file_path, 'r') as f:
            code = f.read()

        # Static analysis
        static_metrics = self._static_analysis(code)

        # AI analysis
        ai_insights = self._ai_analysis(code)

        # Combine results
        final_score = self._calculate_final_score(static_metrics, ai_insights)

        return ComplexityScore(
            score=final_score,
            metrics=static_metrics,
            suggestions=ai_insights['suggestions'],
            suitable_for_beginner=final_score <= 4.0
        )

    def _static_analysis(self, code: str) -> Dict[str, float]:
        """Perform static code analysis."""
        try:
            tree = ast.parse(code)

            metrics = {
                'lines_of_code': len(code.split('\n')),
                'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'complexity': self._cyclomatic_complexity(tree),
            }

            return metrics
        except SyntaxError:
            return {'lines_of_code': 0, 'functions': 0, 'classes': 0, 'complexity': 0}

    def _cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def _ai_analysis(self, code: str) -> Dict:
        """Use GPT-4 to analyze code complexity."""
        prompt = f"""Analyze this code for complexity and provide:
1. Overall complexity rating (0-10)
2. Beginner-friendly aspects
3. Challenging parts
4. Suggestions for improvements

Code:
```python
{code[:2000]}  # Limit to first 2000 chars
```
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a code complexity expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content

        return {
            'ai_score': self._extract_score(content),
            'suggestions': self._extract_suggestions(content)
        }

    def _extract_score(self, content: str) -> float:
        """Extract numerical score from AI response."""
        match = re.search(r'(\d+(\.\d+)?)/10', content)
        return float(match.group(1)) if match else 5.0

    def _extract_suggestions(self, content: str) -> List[str]:
        """Extract suggestions from AI response."""
        lines = content.split('\n')
        suggestions = [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        return suggestions[:5]  # Top 5 suggestions

    def _calculate_final_score(self, static: Dict, ai: Dict) -> float:
        """Combine static and AI scores."""
        # Weight static analysis (40%) and AI analysis (60%)
        static_score = min(10, (
            static['complexity'] * 0.5 +
            static['classes'] * 0.3 +
            static['functions'] * 0.2
        ))

        final = (static_score * 0.4) + (ai['ai_score'] * 0.6)
        return round(final, 2)


# Example usage
if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_file("example.py")
    print(f"Complexity: {result.score}/10")
    print(f"Beginner-friendly: {result.suitable_for_beginner}")
    print(f"Suggestions: {result.suggestions}")
