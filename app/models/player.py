from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class Position(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"

class Player(BaseModel):
    """Player model for fantasy football data"""
    id: str
    name: str
    position: Position
    team: str
    rank: Optional[Union[int, str]] = None
    adp: Optional[Union[float, str]] = None  # Average Draft Position
    projected_points: Optional[Union[float, str]] = None
    value_score: Optional[Union[float, str]] = None
    injury_status: Optional[str] = None
    bye_week: Optional[int] = None
    age: Optional[int] = None
    experience: Optional[int] = None
    
    class Config:
        from_attributes = True

class PlayerAnalysis(BaseModel):
    """Detailed player analysis"""
    player: Player
    strengths: List[str] = []
    weaknesses: List[str] = []
    outlook: str = ""
    risk_level: str = "Medium"
    recommendation: str = ""

class DraftContext(BaseModel):
    """Context for draft decisions"""
    current_round: int
    current_pick: int
    total_teams: int
    user_team_position: int
    league_settings: Dict[str, Any] = {}
    scoring_format: str = "PPR"

class TeamRoster(BaseModel):
    """User's team roster"""
    team_name: str
    players: List[Player] = []
    position_counts: Dict[str, int] = {}
    total_points: float = 0.0

class RecommendationRequest(BaseModel):
    """Request for player recommendations"""
    available_players: List[Player]
    user_team: TeamRoster
    draft_context: DraftContext
    preferences: Optional[Dict[str, Any]] = None

class Recommendation(BaseModel):
    """Player recommendation with reasoning"""
    player: Player
    reasoning: str
    confidence_score: float
    alternatives: List[Player] = []
    risk_assessment: str = ""

class RecommendationResponse(BaseModel):
    """Response with recommendations"""
    primary_recommendation: Recommendation
    alternative_recommendations: List[Recommendation] = []
    strategy_notes: str = ""
    next_picks_suggestion: List[str] = [] 