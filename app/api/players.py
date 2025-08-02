from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging

from app.models.player import Player, PlayerAnalysis, Position
from app.services.player_service import PlayerService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency
def get_player_service() -> PlayerService:
    return PlayerService()

@router.get("/players", response_model=List[Player])
async def get_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(50, description="Number of players to return"),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get list of players with optional filtering
    """
    try:
        if position:
            try:
                pos_enum = Position(position.upper())
                players = player_service.get_players_by_position(pos_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        else:
            players = list(player_service.players_cache.values())
        
        # Sort by rank and limit
        sorted_players = sorted(players, key=lambda p: p.rank or float('inf'))
        return sorted_players[:limit]
        
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving players: {str(e)}")

@router.get("/players/{player_id}", response_model=Player)
async def get_player(
    player_id: str,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get specific player by ID
    """
    try:
        player = player_service.get_player_by_id(player_id)
        if not player:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        return player
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving player: {str(e)}")

@router.get("/players/search/{name}", response_model=List[Player])
async def search_players(
    name: str,
    limit: int = Query(10, description="Number of results to return"),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Search players by name
    """
    try:
        # Simple name search (case-insensitive)
        matching_players = []
        search_name = name.lower()
        
        for player in player_service.players_cache.values():
            if search_name in player.name.lower():
                matching_players.append(player)
        
        # Sort by rank and limit
        sorted_players = sorted(matching_players, key=lambda p: p.rank or float('inf'))
        return sorted_players[:limit]
        
    except Exception as e:
        logger.error(f"Error searching players: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")

@router.get("/players/{player_id}/analysis", response_model=PlayerAnalysis)
async def get_player_analysis(
    player_id: str,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get detailed analysis for a specific player
    """
    try:
        analysis = player_service.get_player_analysis(player_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player analysis for {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving player analysis: {str(e)}")

@router.get("/players/top/{position}", response_model=List[Player])
async def get_top_players_by_position(
    position: str,
    limit: int = Query(20, description="Number of players to return"),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get top players by position
    """
    try:
        try:
            pos_enum = Position(position.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players = player_service.get_top_players(position=pos_enum, limit=limit)
        return players
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top players for {position}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving top players: {str(e)}")

@router.post("/players", response_model=Player)
async def create_player(
    player: Player,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Create a new player
    """
    try:
        player_service.add_player(player)
        return player
        
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating player: {str(e)}")

@router.put("/players/{player_id}", response_model=Player)
async def update_player(
    player_id: str,
    player: Player,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Update an existing player
    """
    try:
        # Ensure the player ID matches
        if player.id != player_id:
            raise HTTPException(status_code=400, detail="Player ID mismatch")
        
        player_service.add_player(player)
        return player
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating player: {str(e)}")

@router.delete("/players/{player_id}")
async def delete_player(
    player_id: str,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Delete a player
    """
    try:
        if player_id not in player_service.players_cache:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        del player_service.players_cache[player_id]
        player_service.save_player_data()
        
        return {"message": f"Player {player_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting player: {str(e)}")

@router.post("/players/bulk", response_model=List[Player])
async def create_players_bulk(
    players: List[Player],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Create multiple players at once
    """
    try:
        player_service.add_players(players)
        return players
        
    except Exception as e:
        logger.error(f"Error creating players bulk: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating players: {str(e)}")

@router.get("/players/positions", response_model=Dict[str, int])
async def get_position_counts(
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get count of players by position
    """
    try:
        position_counts = {}
        for player in player_service.players_cache.values():
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        return position_counts
        
    except Exception as e:
        logger.error(f"Error getting position counts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving position counts: {str(e)}")

@router.post("/players/scrape", response_model=List[Player])
async def scrape_player_data(
    source: str = Query("espn", description="Data source (espn, yahoo)"),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Scrape player data from external sources
    """
    try:
        players = player_service.scrape_player_data(source)
        
        if players:
            player_service.add_players(players)
        
        return players
        
    except Exception as e:
        logger.error(f"Error scraping player data: {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping player data: {str(e)}")

@router.post("/players/sync/sleeper", response_model=List[Player])
async def sync_sleeper_players(
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Sync player data from Sleeper API
    """
    try:
        players = player_service.sync_with_sleeper_api()
        return players
        
    except Exception as e:
        logger.error(f"Error syncing with Sleeper API: {e}")
        raise HTTPException(status_code=500, detail=f"Error syncing with Sleeper API: {str(e)}")

@router.post("/players/sync/espn", response_model=List[Player])
async def sync_espn_players(
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Sync player data from ESPN API
    """
    try:
        players = player_service.sync_with_sleeper_api()
        return players
        
    except Exception as e:
        logger.error(f"Error syncing with Sleeper API: {e}")
        raise HTTPException(status_code=500, detail=f"Error syncing with Sleeper API: {str(e)}")

@router.post("/players/enrich", response_model=List[Player])
async def enrich_players(
    request: Dict[str, Any],
    source: str = Query("sleeper", description="Data source (sleeper, espn)"),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Enrich player data with API information
    """
    try:
        # Extract players from request body
        players_data = request.get("players", [])
        
        # Convert to Player objects
        players = []
        for player_data in players_data:
            try:
                player = Player(**player_data)
                players.append(player)
            except Exception as e:
                logger.warning(f"Invalid player data: {e}")
                continue
        
        enriched_players = player_service.get_enriched_players(players, source)
        return enriched_players
        
    except Exception as e:
        logger.error(f"Error enriching players: {e}")
        raise HTTPException(status_code=500, detail=f"Error enriching players: {str(e)}")

@router.post("/players/update-rankings")
async def update_player_rankings(
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Update player rankings from external APIs
    """
    try:
        player_service.update_player_rankings()
        return {"message": "Player rankings updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating player rankings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating player rankings: {str(e)}")

@router.get("/players/health")
async def players_health():
    """
    Health check for players service
    """
    return {
        "status": "healthy",
        "service": "players",
        "cache_size": len(PlayerService().players_cache)
    } 

@router.post("/players/sync")
async def sync_player_data(
    source: str = "sleeper",
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Sync player data from external APIs to populate missing stats
    """
    try:
        logger.info(f"Starting player data sync from {source}")
        
        if source == "sleeper":
            players = player_service.sync_with_sleeper_api()
        elif source == "espn":
            players = player_service.sync_with_sleeper_api()  # ESPN endpoint now uses Sleeper
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        # Enrich existing players with API data
        enriched_count = 0
        for player in player_service.players_cache.values():
            if not player.projected_points or not player.last_year_points:
                enriched_player = player_service.enrich_player_with_api_data(player, source)
                if enriched_player and (enriched_player.projected_points or enriched_player.last_year_points):
                    enriched_count += 1
        
        logger.info(f"Synced {len(players)} players, enriched {enriched_count} existing players")
        
        return {
            "message": f"Player data synced successfully from {source}",
            "total_players": len(players),
            "enriched_players": enriched_count
        }
        
    except Exception as e:
        logger.error(f"Error syncing player data: {e}")
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@router.post("/players/enrich-specific")
async def enrich_specific_players(
    player_names: List[str],
    source: str = "sleeper",
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Enrich specific players with API data
    """
    try:
        enriched_players = []
        
        for name in player_names:
            player = player_service.get_player_by_name(name)
            if player:
                enriched_player = player_service.enrich_player_with_api_data(player, source)
                if enriched_player:
                    enriched_players.append(enriched_player)
        
        return {
            "message": f"Enriched {len(enriched_players)} players",
            "enriched_players": [p.name for p in enriched_players]
        }
        
    except Exception as e:
        logger.error(f"Error enriching players: {e}")
        raise HTTPException(status_code=500, detail=f"Enrichment error: {str(e)}")

@router.get("/players/stats/{player_name}")
async def get_player_stats(
    player_name: str,
    source: str = "sleeper",
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get detailed stats for a specific player
    """
    try:
        player = player_service.get_player_by_name(player_name)
        if not player:
            raise HTTPException(status_code=404, detail=f"Player {player_name} not found")
        
        # Try to enrich with API data
        enriched_player = player_service.enrich_player_with_api_data(player, source)
        
        return {
            "player": enriched_player.dict(),
            "has_projected_points": enriched_player.projected_points is not None,
            "has_last_year_points": enriched_player.last_year_points is not None,
            "has_value_score": enriched_player.value_score is not None
        }
        
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}") 

@router.post("/players/populate-mock")
async def populate_mock_data(
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Populate mock data for players missing stats (for testing)
    """
    try:
        updated_count = player_service.populate_mock_data()
        
        return {
            "message": f"Populated mock data for {updated_count} players",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error populating mock data: {e}")
        raise HTTPException(status_code=500, detail=f"Mock data error: {str(e)}") 

@router.post("/players/enrich-sleeper")
async def enrich_players_from_sleeper(
    player_names: List[str],
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Enrich specific players with real data from Sleeper API
    """
    try:
        logger.info(f"Enriching {len(player_names)} players from Sleeper API")
        
        enriched_players = player_service.enrich_players_from_sleeper(player_names)
        
        return {
            "message": f"Enriched {len(enriched_players)} players with real Sleeper data",
            "enriched_players": [p.name for p in enriched_players],
            "players_with_stats": [p.name for p in enriched_players if p.projected_points or p.last_year_points]
        }
        
    except Exception as e:
        logger.error(f"Error enriching players from Sleeper: {e}")
        raise HTTPException(status_code=500, detail=f"Sleeper enrichment error: {str(e)}")

@router.get("/players/sleeper/{player_name}")
async def get_sleeper_player(
    player_name: str,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Get real player data from Sleeper API by name
    """
    try:
        player = player_service.get_sleeper_player_by_name(player_name)
        
        if not player:
            raise HTTPException(status_code=404, detail=f"Player {player_name} not found in Sleeper")
        
        return {
            "player": player.dict(),
            "has_projected_points": player.projected_points is not None,
            "has_last_year_points": player.last_year_points is not None,
            "has_value_score": player.value_score is not None,
            "source": "sleeper"
        }
        
    except Exception as e:
        logger.error(f"Error getting Sleeper player: {e}")
        raise HTTPException(status_code=500, detail=f"Sleeper player error: {str(e)}") 