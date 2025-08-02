from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.models.player import RecommendationRequest, RecommendationResponse, Player
from app.services.rag_service import RAGService
from app.services.player_service import PlayerService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependencies
def get_rag_service() -> RAGService:
    return RAGService()

def get_player_service() -> PlayerService:
    return PlayerService()

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    rag_service: RAGService = Depends(get_rag_service),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get intelligent player recommendations based on current draft state
    """
    try:
        print("🔍 DEBUG: Recommendations endpoint called")
        logger.info(f"🎯 Recommendation request for {len(request.available_players)} available players")
        
        # Log original player data
        print("🔍 DEBUG: Original player data:")
        for i, player in enumerate(request.available_players[:3]):  # Log first 3 players
            print(f"   {i+1}. {player.name} - proj={player.projected_points}, value={player.value_score}")
            logger.info(f"📋 Original player {i+1}: {player.name} - proj={player.projected_points}, value={player.value_score}")
        
        # Enrich available players with real Sleeper data
        print("🔍 DEBUG: Starting player enrichment from Sleeper API...")
        logger.info(f"🔍 Starting player enrichment from Sleeper API...")
        enriched_players = player_service.enrich_recommendation_players(request.available_players)
        
        # Log enriched player data
        print("🔍 DEBUG: Enriched player data:")
        logger.info(f"📊 Enrichment complete. Checking enriched players...")
        for i, player in enumerate(enriched_players[:3]):  # Log first 3 players
            print(f"   {i+1}. {player.name} - proj={player.projected_points}, value={player.value_score}")
            logger.info(f"📋 Enriched player {i+1}: {player.name} - proj={player.projected_points}, value={player.value_score}")
        
        # Update the request with enriched players
        request.available_players = enriched_players
        print(f"🔍 DEBUG: Updated request with {len(enriched_players)} enriched players")
        
        # Get recommendations from RAG service
        print("🔍 DEBUG: Getting recommendations from RAG service...")
        logger.info(f"🤖 Getting recommendations from RAG service...")
        response = rag_service.get_recommendations(
            available_players=request.available_players,
            user_team=request.user_team.dict(),
            draft_context=request.draft_context.dict()
        )
        
        # Log recommendation results
        if response.primary_recommendation:
            primary = response.primary_recommendation.player
            print(f"🔍 DEBUG: Primary recommendation: {primary.name} - proj={primary.projected_points}, value={primary.value_score}")
            logger.info(f"🏆 Primary recommendation: {primary.name} - proj={primary.projected_points}, value={primary.value_score}")
        
        print("🔍 DEBUG: Recommendations generated successfully")
        logger.info("✅ Recommendations generated successfully with real player data")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in recommendations endpoint: {e}")
        print(f"❌ DEBUG: Exception in recommendations endpoint: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")

@router.get("/recommendations/cache/clear")
async def clear_recommendation_cache(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Clear recommendation cache
    """
    try:
        rag_service.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")

@router.get("/recommendations/cache/reset")
async def reset_recommendation_cache(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Reset the RAG service singleton (for testing)
    """
    try:
        RAGService.reset_singleton()
        return {"message": "RAG service singleton reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting singleton: {e}")
        raise HTTPException(status_code=500, detail=f"Singleton reset error: {str(e)}")

@router.get("/recommendations/cache/status")
async def get_cache_status(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get cache status and statistics
    """
    try:
        stats = rag_service.get_cache_stats()
        
        # Add more detailed cache information
        recommendation_cache_keys = list(rag_service.recommendation_cache.keys())
        chat_cache_keys = list(rag_service.chat_cache.keys())
        stats.update({
            "recommendation_cache_keys_sample": [key[:50] + "..." for key in recommendation_cache_keys[:5]],
            "chat_cache_keys_sample": [key[:50] + "..." for key in chat_cache_keys[:5]],
            "total_recommendation_cache_keys": len(recommendation_cache_keys),
            "total_chat_cache_keys": len(chat_cache_keys),
            "is_singleton": rag_service._instance is not None
        })
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Cache status error: {str(e)}")

@router.get("/recommendations/position/{position}", response_model=List[Player])
async def get_position_recommendations(
    position: str,
    limit: int = 10,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get top players by position
    """
    try:
        from app.models.player import Position
        
        # Convert string to Position enum
        try:
            pos_enum = Position(position.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players = player_service.get_players_by_position(pos_enum)
        top_players = sorted(players, key=lambda p: p.rank or float('inf'))[:limit]
        
        return top_players
        
    except Exception as e:
        logger.error(f"Error getting position recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Position recommendation error: {str(e)}")

@router.get("/recommendations/value", response_model=List[Player])
async def get_value_recommendations(
    available_players: List[Player],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get players with good value (ADP vs rank)
    """
    try:
        value_players = player_service.get_value_opportunities(available_players)
        return value_players[:10]  # Return top 10 value players
        
    except Exception as e:
        logger.error(f"Error getting value recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Value recommendation error: {str(e)}")

@router.get("/recommendations/scarcity", response_model=Dict[str, str])
async def get_positional_scarcity(
    available_players: List[Player],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get positional scarcity analysis
    """
    try:
        scarcity = player_service.get_positional_scarcity(available_players)
        return scarcity
        
    except Exception as e:
        logger.error(f"Error getting positional scarcity: {e}")
        raise HTTPException(status_code=500, detail=f"Scarcity analysis error: {str(e)}")

@router.get("/recommendations/risk", response_model=List[Player])
async def get_risk_players(
    available_players: List[Player],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get players with risk factors
    """
    try:
        risk_players = player_service.get_risk_players(available_players)
        return risk_players[:10]  # Return top 10 risk players
        
    except Exception as e:
        logger.error(f"Error getting risk players: {e}")
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")

@router.post("/recommendations/compare", response_model=List[Dict[str, Any]])
async def compare_players(
    player_ids: List[str],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Compare multiple players side by side
    """
    try:
        comparisons = player_service.get_player_comparison(player_ids)
        
        # Convert to dict format for easier frontend consumption
        result = []
        for analysis in comparisons:
            result.append({
                "player": analysis.player.dict(),
                "strengths": analysis.strengths,
                "weaknesses": analysis.weaknesses,
                "outlook": analysis.outlook,
                "risk_level": analysis.risk_level,
                "recommendation": analysis.recommendation
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing players: {e}")
        raise HTTPException(status_code=500, detail=f"Player comparison error: {str(e)}")

@router.get("/recommendations/strategy/{draft_round}", response_model=Dict[str, Any])
async def get_draft_strategy(
    draft_round: int,
    user_team: Dict[str, Any],
    available_players: List[Player]
):
    """
    Get draft strategy recommendations for specific round
    """
    try:
        # This would contain round-specific strategy advice
        strategies = {
            1: {
                "focus": "Best Player Available",
                "positions": ["RB", "WR"],
                "advice": "Take the highest ranked player regardless of position"
            },
            2: {
                "focus": "Positional Balance",
                "positions": ["RB", "WR", "TE"],
                "advice": "Consider positional scarcity and team needs"
            },
            3: {
                "focus": "Value Picks",
                "positions": ["WR", "RB", "QB"],
                "advice": "Look for players falling below their ADP"
            }
        }
        
        strategy = strategies.get(draft_round, {
            "focus": "General Strategy",
            "positions": ["Any"],
            "advice": "Focus on best available player and team needs"
        })
        
        # Add positional analysis
        position_counts = {}
        for player in user_team.get("players", []):
            pos = player.get("position")
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        strategy["current_team"] = {
            "position_counts": position_counts,
            "total_players": len(user_team.get("players", []))
        }
        
        return strategy
        
    except Exception as e:
        logger.error(f"Error getting draft strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy error: {str(e)}")

@router.get("/recommendations/health")
async def recommendations_health():
    """
    Health check for recommendations service
    """
    return {
        "status": "healthy",
        "service": "recommendations",
        "rag_available": True,
        "player_service_available": True
    } 