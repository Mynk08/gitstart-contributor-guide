"""
FastAPI application entry point.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from src.ai_engine.code_analyzer import CodeAnalyzer
from src.ml_models.issue_classifier import IssueDifficultyClassifier
from src.database import get_db
from src.models import Issue, Repository
from src.schemas import IssueCreate, IssueResponse, AnalysisRequest, AnalysisResponse

app = FastAPI(
    title="GitStart API",
    description="AI-powered contributor onboarding platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
code_analyzer = CodeAnalyzer()
issue_classifier = IssueDifficultyClassifier()


@app.get("/")
async def root():
    return {"message": "GitStart API", "version": "1.0.0"}


@app.post("/api/v1/analyze/code", response_model=AnalysisResponse)
async def analyze_code(request: AnalysisRequest):
    """Analyze code complexity using AI."""
    try:
        result = code_analyzer.analyze_file(request.file_path)
        return AnalysisResponse(
            score=result.score,
            metrics=result.metrics,
            suggestions=result.suggestions,
            beginner_friendly=result.suitable_for_beginner
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/issues/classify")
async def classify_issue(issue_text: str):
    """Classify issue difficulty using ML."""
    difficulty, confidence = issue_classifier.predict(issue_text)
    return {
        "difficulty": difficulty,
        "confidence": confidence,
        "recommended_for_beginners": difficulty == "beginner"
    }


@app.get("/api/v1/issues/beginner", response_model=List[IssueResponse])
async def get_beginner_issues(db: Session = Depends(get_db), limit: int = 20):
    """Get beginner-friendly issues."""
    issues = db.query(Issue).filter(Issue.difficulty == "beginner").limit(limit).all()
    return issues


@app.get("/health")
async def health_check():
    return {"status": "healthy", "ai_engine": "operational"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
