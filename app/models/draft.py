from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .player import Player, Position

class DraftPick(BaseModel):
    """Individual draft pick"""
    pick_number: int
    round: int
    team_position: int
    player: Optional[Player] = None
    timestamp: Optional[datetime] = None

class DraftBoard(BaseModel):
    """Complete draft board state"""
    total_teams: int
    total_rounds: int
    current_round: int
    current_pick: int
    picks: List[DraftPick] = []
    available_players: List[Player] = []
    drafted_players: List[Player] = []

class TeamDraftState(BaseModel):
    """Team's current draft state"""
    team_name: str
    team_position: int
    picks_made: List[DraftPick] = []
    next_pick: Optional[int] = None
    position_needs: Dict[str, int] = {}
    strategy: Optional[str] = None

class DraftSettings(BaseModel):
    """League draft settings"""
    league_name: str
    scoring_format: str = "PPR"  # PPR, Standard, Half-PPR
    roster_positions: Dict[str, int] = {
        "QB": 1,
        "RB": 2,
        "WR": 2,
        "TE": 1,
        "FLEX": 1,
        "K": 1,
        "DEF": 1
    }
    bench_slots: int = 6
    total_teams: int = 12
    snake_draft: bool = True
    time_per_pick: int = 90  # seconds

class DraftAnalysis(BaseModel):
    """Analysis of draft state"""
    positional_scarcity: Dict[str, str] = {}  # "High", "Medium", "Low"
    value_opportunities: List[Player] = []
    risk_players: List[Player] = []
    recommended_strategy: str = ""
    next_round_focus: List[str] = [] 