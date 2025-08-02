import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from app.models.player import Player, PlayerAnalysis, Position
from app.services.api_service import APIService

logger = logging.getLogger(__name__)

class PlayerService:
    """Service for managing player data and analysis"""
    
    def __init__(self):
        self.players_cache = {}
        self.player_data_path = "./data/players.json"
        self.api_service = APIService()
        self.load_player_data()
    
    def load_player_data(self):
        """Load player data from file"""
        try:
            if os.path.exists(self.player_data_path):
                with open(self.player_data_path, 'r') as f:
                    data = json.load(f)
                    for player_data in data:
                        player = Player(**player_data)
                        self.players_cache[player.id] = player
                logger.info(f"Loaded {len(self.players_cache)} players from cache")
        except Exception as e:
            logger.error(f"Error loading player data: {e}")
    
    def save_player_data(self):
        """Save player data to file"""
        try:
            os.makedirs(os.path.dirname(self.player_data_path), exist_ok=True)
            with open(self.player_data_path, 'w') as f:
                json.dump([player.dict() for player in self.players_cache.values()], f, indent=2)
            logger.info(f"Saved {len(self.players_cache)} players to cache")
        except Exception as e:
            logger.error(f"Error saving player data: {e}")
    
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        return self.players_cache.get(player_id)
    
    def get_player_by_name(self, player_name: str) -> Optional[Player]:
        """Get player data by name from Sleeper API"""
        try:
            logger.info(f"🔍 PlayerService: Getting player by name: '{player_name}'")
            
            api_service = APIService()
            player = api_service.get_sleeper_player_by_name(player_name)
            
            if player:
                logger.info(f"✅ PlayerService: Found player '{player.name}' in Sleeper API")
                return player
            else:
                logger.warning(f"❌ PlayerService: Player '{player_name}' not found in Sleeper API")
                return None
                
        except Exception as e:
            logger.error(f"❌ PlayerService: Error getting player by name: {e}")
            return None

    def get_all_players(self) -> List[Player]:
        """Get all players from Sleeper API"""
        try:
            logger.info("🔍 PlayerService: Getting all players from Sleeper API")
            
            api_service = APIService()
            players = api_service.get_sleeper_players()
            
            logger.info(f"✅ PlayerService: Retrieved {len(players)} players from Sleeper API")
            return players
            
        except Exception as e:
            logger.error(f"❌ PlayerService: Error getting all players: {e}")
            return []
    
    def get_players_by_position(self, position: Position) -> List[Player]:
        """Get all players by position"""
        return [player for player in self.players_cache.values() if player.position == position]
    
    def get_top_players(self, position: Optional[Position] = None, limit: int = 50) -> List[Player]:
        """Get top players by rank"""
        players = self.players_cache.values()
        
        if position:
            players = [p for p in players if p.position == position]
        
        # Sort by rank (lower is better)
        sorted_players = sorted(players, key=lambda p: p.rank or float('inf'))
        return sorted_players[:limit]
    
    def add_player(self, player: Player):
        """Add or update player in cache"""
        self.players_cache[player.id] = player
        self.save_player_data()
    
    def add_players(self, players: List[Player]):
        """Add multiple players to cache"""
        for player in players:
            self.players_cache[player.id] = player
        self.save_player_data()
    
    def enrich_player_with_api_data(self, player: Player, source: str = "sleeper") -> Player:
        """Enrich player data with real API data - Sleeper as primary source"""
        try:
            # First try to get from cache
            cached_player = self.get_player_by_name(player.name)
            if cached_player and cached_player.projected_points and cached_player.last_year_points:
                return cached_player
            
            # Try Sleeper API
            logger.info(f"🔍 Enriching {player.name} with Sleeper data")
            enriched_player = self.api_service.get_sleeper_player_by_name(player.name)
            
            if enriched_player and (enriched_player.projected_points or enriched_player.last_year_points):
                logger.info(f"✅ Found Sleeper data for {player.name}: proj={enriched_player.projected_points}, last={enriched_player.last_year_points}")
                # Cache the enriched player
                self.add_player(enriched_player)
                return enriched_player
            
            # If no Sleeper data, return original player
            logger.warning(f"⚠️ No Sleeper data found for {player.name}, keeping original")
            return player
            
        except Exception as e:
            logger.error(f"Error enriching player {player.name}: {e}")
            return player
    
    def get_enriched_players(self, players: List[Player], source: str = "espn") -> List[Player]:
        """Enrich a list of players with API data - ESPN as primary source"""
        enriched_players = []
        
        for player in players:
            enriched_player = self.enrich_player_with_api_data(player, source)
            enriched_players.append(enriched_player)
        
        return enriched_players
    
    def sync_with_sleeper_api(self) -> List[Player]:
        """Sync player data with Sleeper API"""
        try:
            logger.info("Syncing with Sleeper API...")
            players = self.api_service.get_sleeper_players()
            
            if players:
                self.add_players(players)
                logger.info(f"Synced {len(players)} players from Sleeper")
            
            return players
            
        except Exception as e:
            logger.error(f"Error syncing with Sleeper API: {e}")
            return []
    
    def get_player_analysis(self, player_id: str) -> Optional[PlayerAnalysis]:
        """Get detailed analysis for a specific player"""
        try:
            player = self.get_player_by_id(player_id)
            if not player:
                return None
            
            # Enrich player data if needed
            player = self.enrich_player_with_api_data(player)
            
            strengths = []
            weaknesses = []
            
            # Analyze based on available data
            if player.projected_points and player.last_year_points:
                if player.projected_points > player.last_year_points:
                    strengths.append("Projected improvement over last year")
                elif player.projected_points < player.last_year_points * 0.9:
                    weaknesses.append("Projected decline from last year")
            
            if player.value_score:
                if player.value_score > 8.0:
                    strengths.append("Excellent value score")
                elif player.value_score < 5.0:
                    weaknesses.append("Low value score")
            
            if player.adp and player.rank:
                adp_rank_diff = player.adp - player.rank
                if adp_rank_diff > 20:
                    strengths.append("Significantly undervalued (ADP much higher than rank)")
                elif adp_rank_diff < -10:
                    weaknesses.append("Potentially overvalued (ADP lower than rank)")
            
            if player.injury_status and player.injury_status != "Healthy":
                weaknesses.append(f"Injury concern: {player.injury_status}")
            
            if player.age and player.age > 30:
                weaknesses.append("Age-related risk")
            
            # Generate outlook
            if len(strengths) > len(weaknesses):
                outlook = "Positive outlook with more strengths than concerns"
            elif len(weaknesses) > len(strengths):
                outlook = "Some concerns to consider before drafting"
            else:
                outlook = "Balanced profile with mixed indicators"
            
            # Determine risk level
            risk_factors = len(weaknesses)
            if risk_factors >= 3:
                risk_level = "High"
            elif risk_factors >= 1:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Generate recommendation
            if len(strengths) > len(weaknesses):
                recommendation = f"Strong pick - {player.name} offers good value at their current ADP."
            elif len(weaknesses) > len(strengths):
                recommendation = f"Proceed with caution - {player.name} has some concerns to consider."
            else:
                recommendation = f"Solid pick - {player.name} is a reasonable selection at their ADP."
            
            return PlayerAnalysis(
                player=player,
                strengths=strengths,
                weaknesses=weaknesses,
                outlook=outlook,
                risk_level=risk_level,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error getting player analysis: {e}")
            return None
    
    def get_positional_scarcity(self, available_players: List[Player]) -> Dict[str, str]:
        """Analyze positional scarcity in available players"""
        position_counts = {}
        for player in available_players:
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        scarcity = {}
        for pos in Position:
            count = position_counts.get(pos, 0)
            if count <= 5:
                scarcity[pos] = "High"
            elif count <= 15:
                scarcity[pos] = "Medium"
            else:
                scarcity[pos] = "Low"
        
        return scarcity
    
    def get_value_opportunities(self, available_players: List[Player]) -> List[Player]:
        """Find players with good value (ADP significantly higher than rank)"""
        value_players = []
        
        for player in available_players:
            if player.adp and player.rank:
                adp_rank_diff = player.adp - player.rank
                if adp_rank_diff > 20:  # ADP 20+ spots higher than rank
                    value_players.append(player)
        
        # Sort by value (biggest difference first)
        value_players.sort(key=lambda p: p.adp - p.rank, reverse=True)
        return value_players
    
    def get_risk_players(self, available_players: List[Player]) -> List[Player]:
        """Find players with risk factors"""
        risk_players = []
        
        for player in available_players:
            risk_factors = []
            
            # Injury risk
            if player.injury_status and player.injury_status != "Healthy":
                risk_factors.append("Injury")
            
            # Age risk
            if player.age and player.age > 30:
                risk_factors.append("Age")
            
            # ADP vs rank risk (overvalued)
            if player.adp and player.rank:
                adp_rank_diff = player.adp - player.rank
                if adp_rank_diff < -10:
                    risk_factors.append("Overvalued")
            
            if risk_factors:
                risk_players.append(player)
        
        return risk_players
    
    def scrape_player_data(self, source: str = "espn") -> List[Player]:
        """Scrape player data from external sources"""
        try:
            if source == "espn":
                return self.sync_with_sleeper_api()
            else:
                logger.error(f"Unknown data source: {source}")
                return []
        except Exception as e:
            logger.error(f"Error scraping player data: {e}")
            return []
    
    def update_player_rankings(self):
        """Update player rankings from external sources"""
        try:
            logger.info("Updating player rankings from APIs...")
            
            # Sync with ESPN API
            sleeper_players = self.sync_with_sleeper_api()
            
            total_updated = len(sleeper_players)
            logger.info(f"Updated {total_updated} players from APIs")
            
        except Exception as e:
            logger.error(f"Error updating player rankings: {e}")
    
    def get_player_comparison(self, player_ids: List[str]) -> List[PlayerAnalysis]:
        """Compare multiple players"""
        comparisons = []
        for player_id in player_ids:
            analysis = self.get_player_analysis(player_id)
            if analysis:
                comparisons.append(analysis)
        return comparisons 
    
    def populate_mock_data(self):
        """Populate mock data for players missing stats"""
        try:
            updated_count = 0
            
            for player in self.players_cache.values():
                if not player.projected_points or not player.last_year_points:
                    # Generate mock data based on position and experience
                    mock_data = self._generate_mock_stats(player)
                    
                    # Update player with mock data
                    player_dict = player.dict()
                    player_dict.update(mock_data)
                    
                    updated_player = Player(**player_dict)
                    self.players_cache[player.id] = updated_player
                    updated_count += 1
            
            # Save updated data
            self.save_player_data()
            logger.info(f"Populated mock data for {updated_count} players")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error populating mock data: {e}")
            return 0
    
    def _generate_mock_stats(self, player: Player) -> Dict[str, Any]:
        """Generate realistic mock stats based on player position and experience"""
        import random
        
        # Base stats by position
        position_stats = {
            "QB": {"min_proj": 200, "max_proj": 350, "min_last": 180, "max_last": 320},
            "RB": {"min_proj": 150, "max_proj": 280, "min_last": 130, "max_last": 260},
            "WR": {"min_proj": 120, "max_proj": 220, "min_last": 100, "max_last": 200},
            "TE": {"min_proj": 80, "max_proj": 150, "min_last": 70, "max_last": 140},
            "K": {"min_proj": 120, "max_proj": 160, "min_last": 110, "max_last": 150},
            "DEF": {"min_proj": 100, "max_proj": 140, "min_last": 90, "max_last": 130}
        }
        
        stats = position_stats.get(player.position, position_stats["WR"])
        
        # Generate projected points
        projected_points = random.uniform(stats["min_proj"], stats["max_proj"])
        
        # Generate last year points (slightly lower for rookies, higher for veterans)
        experience_factor = min(player.experience or 1, 8) / 8.0
        last_year_points = projected_points * (0.8 + 0.4 * experience_factor)
        
        # Generate value score (0-10 scale)
        value_score = random.uniform(5.0, 9.5)
        
        # Generate rank based on projected points (lower is better)
        rank = max(1, int(300 - projected_points / 2))
        
        # Generate ADP (average draft position)
        adp = max(1, int(rank * random.uniform(0.8, 1.2)))
        
        return {
            "projected_points": round(projected_points, 1),
            "last_year_points": round(last_year_points, 1),
            "value_score": round(value_score, 1),
            "rank": rank,
            "adp": adp
        }
    
    def enrich_recommendation_players(self, available_players: List[Player]) -> List[Player]:
        """Enrich players used in recommendations with Sleeper data only"""
        try:
            print("🔍 DEBUG: enrich_recommendation_players() called")
            player_names = [player.name for player in available_players if player.name]
            if not player_names:
                logger.warning(f"⚠️ PlayerService: No player names found in available players")
                print("❌ DEBUG: No player names found")
                return available_players

            print(f"🔍 DEBUG: Enriching {len(player_names)} players: {player_names[:3]}...")
            logger.info(f"🔍 PlayerService: Enriching {len(player_names)} recommendation players with Sleeper data only")

            # Get Sleeper players by names
            api_service = APIService()
            print("🔍 DEBUG: Calling Sleeper API for player data...")
            sleeper_players = api_service.get_sleeper_players_by_names(player_names)
            print(f"🔍 DEBUG: Retrieved {len(sleeper_players)} players from Sleeper API")
            
            # Create lookup for Sleeper players
            sleeper_lookup = {player.name.lower(): player for player in sleeper_players}
            print(f"🔍 DEBUG: Created lookup with {len(sleeper_lookup)} Sleeper players")
            
            enriched_players = []
            
            for player in available_players:
                print(f"🔍 DEBUG: Processing player: {player.name}")
                logger.info(f"🔍 Processing recommendation player: {player.name}")
                
                # Try to find Sleeper data for this player
                sleeper_player = sleeper_lookup.get(player.name.lower())
                
                if sleeper_player:
                    print(f"🔍 DEBUG: Found Sleeper data for {player.name}")
                    # Prioritize scraped data over Sleeper API data
                    # Use scraped projected_points if available, otherwise use Sleeper
                    projected_points = player.projected_points if player.projected_points and player.projected_points != "N/A" else sleeper_player.projected_points
                    
                    # Use real Sleeper data for other fields
                    enriched_player = Player(
                        id=player.id,
                        name=player.name,
                        position=player.position,
                        team=player.team,
                        rank=sleeper_player.rank,
                        adp=sleeper_player.adp,
                        projected_points=projected_points,  # Prioritize scraped data
                        value_score=sleeper_player.value_score,
                        injury_status=sleeper_player.injury_status,
                        bye_week=player.bye_week,  # Keep scraped bye week
                        age=sleeper_player.age,
                        experience=sleeper_player.experience
                    )
                    print(f"🔍 DEBUG: Enriched {player.name} with data: rank={sleeper_player.rank}, adp={sleeper_player.adp}, proj={projected_points} (scraped: {player.projected_points})")
                    logger.info(f"✅ Found real Sleeper data for {player.name}")
                else:
                    print(f"🔍 DEBUG: No Sleeper data found for {player.name}, keeping scraped data")
                    # Keep the scraped data as-is
                    enriched_player = Player(
                        id=player.id,
                        name=player.name,
                        position=player.position,
                        team=player.team,
                        rank=player.rank,
                        adp=player.adp,
                        projected_points=player.projected_points,  # Keep scraped projected points
                        value_score=player.value_score,
                        injury_status=player.injury_status,
                        bye_week=player.bye_week,
                        age=player.age,
                        experience=player.experience
                    )
                    logger.info(f"❌ No Sleeper data found for {player.name}, keeping scraped data")
                
                enriched_players.append(enriched_player)

            print(f"🔍 DEBUG: Enrichment complete. {len(enriched_players)} players processed")
            logger.info(f"✅ PlayerService: Enriched {len(enriched_players)} recommendation players with real Sleeper data only")
            return enriched_players

        except Exception as e:
            logger.error(f"❌ PlayerService: Error enriching recommendation players: {e}")
            print(f"❌ DEBUG: Exception in enrich_recommendation_players: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")

            # Return original players with scraped data if enrichment fails completely
            fallback_players = []
            for player in available_players:
                fallback_player = Player(
                    id=player.id,
                    name=player.name,
                    position=player.position,
                    team=player.team,
                    rank=player.rank,
                    adp=player.adp,
                    projected_points=player.projected_points,  # Keep scraped projected points
                    value_score=player.value_score,
                    injury_status=player.injury_status,
                    bye_week=player.bye_week,
                    age=player.age,
                    experience=player.experience
                )
                fallback_players.append(fallback_player)

            print(f"🔍 DEBUG: Using fallback with {len(fallback_players)} players (keeping scraped data)")
            logger.info(f"🔄 Returning {len(fallback_players)} players with scraped data due to enrichment failure")
            return fallback_players 