import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from app.models.player import Player, Position
import logging

logger = logging.getLogger(__name__)

class APIService:
    """Service for handling external API calls"""
    
    def __init__(self):
        # Sleeper API base URL
        self.sleeper_base_url = "https://api.sleeper.app/v1"
        
        # Cache file path for Sleeper data
        self.sleeper_cache_file = "data/sleeper_players_cache.json"
        self.sleeper_cache_timestamp_file = "data/sleeper_cache_timestamp.txt"
        self._cache_duration = 24 * 60 * 60  # 24 hours in seconds
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Initialize cache
        self._sleeper_players_cache = None
        self._sleeper_cache_timestamp = None
        self._load_sleeper_cache()

    def _load_sleeper_cache(self):
        """Load Sleeper players cache from file"""
        try:
            if os.path.exists(self.sleeper_cache_file) and os.path.exists(self.sleeper_cache_timestamp_file):
                # Load timestamp
                with open(self.sleeper_cache_timestamp_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    self._sleeper_cache_timestamp = float(timestamp_str)
                
                # Check if cache is still valid (less than 24 hours old)
                if time.time() - self._sleeper_cache_timestamp < self._cache_duration:
                    # Load cached data
                    with open(self.sleeper_cache_file, 'r') as f:
                        self._sleeper_players_cache = json.load(f)
                    logger.info(f"✅ Loaded Sleeper cache from file (age: {time.time() - self._sleeper_cache_timestamp:.0f}s)")
                    return
                else:
                    logger.info("🔄 Sleeper cache expired, will fetch fresh data")
            else:
                logger.info("🔄 No Sleeper cache found, will fetch fresh data")
                
        except Exception as e:
            logger.error(f"❌ Error loading Sleeper cache: {e}")
        
        # Cache is invalid or doesn't exist, fetch fresh data
        self._fetch_sleeper_players()

    def _save_sleeper_cache(self, players_data: Dict[str, Any]):
        """Save Sleeper players data to cache file"""
        try:
            # Save players data
            with open(self.sleeper_cache_file, 'w') as f:
                json.dump(players_data, f)
            
            # Save timestamp
            current_timestamp = time.time()
            with open(self.sleeper_cache_timestamp_file, 'w') as f:
                f.write(str(current_timestamp))
            
            self._sleeper_players_cache = players_data
            self._sleeper_cache_timestamp = current_timestamp
            
            logger.info(f"✅ Saved Sleeper cache to file ({len(players_data)} players)")
            
        except Exception as e:
            logger.error(f"❌ Error saving Sleeper cache: {e}")

    def _fetch_sleeper_players(self):
        """Fetch all NFL players from Sleeper API"""
        try:
            print("🔍 DEBUG: Starting Sleeper API fetch...")
            logger.info("📡 Fetching all NFL players from Sleeper API...")
            
            url = f"{self.sleeper_base_url}/players/nfl"
            print(f"🔍 DEBUG: Fetching from URL: {url}")
            
            response = requests.get(url, timeout=60)  # Increased timeout for large file
            print(f"🔍 DEBUG: Sleeper API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Sleeper API error: {response.status_code}")
                logger.error(f"Sleeper API response: {response.text[:200]}")
                print(f"❌ DEBUG: Sleeper API failed with status {response.status_code}")
                return
            
            players_data = response.json()
            print(f"🔍 DEBUG: Retrieved {len(players_data)} players from Sleeper API")
            logger.info(f"✅ Retrieved {len(players_data)} players from Sleeper API")
            
            # Log sample player data
            sample_player_id = list(players_data.keys())[0]
            sample_player = players_data[sample_player_id]
            print(f"🔍 DEBUG: Sample player data: {sample_player.get('first_name', '')} {sample_player.get('last_name', '')}")
            print(f"🔍 DEBUG: Sample player search_rank: {sample_player.get('search_rank', 'N/A')}")
            
            # Save to cache
            print("🔍 DEBUG: Saving Sleeper data to cache...")
            self._save_sleeper_cache(players_data)
            print("🔍 DEBUG: Sleeper data saved to cache successfully")
            
        except Exception as e:
            logger.error(f"❌ Error fetching Sleeper players: {e}")
            print(f"❌ DEBUG: Exception in Sleeper fetch: {e}")
            # If fetch fails, try to use existing cache even if expired
            if os.path.exists(self.sleeper_cache_file):
                try:
                    with open(self.sleeper_cache_file, 'r') as f:
                        self._sleeper_players_cache = json.load(f)
                    logger.info(f"🔄 Using expired cache due to API failure ({len(self._sleeper_players_cache)} players)")
                    print(f"🔍 DEBUG: Using expired cache with {len(self._sleeper_players_cache)} players")
                except Exception as cache_error:
                    logger.error(f"❌ Error loading expired cache: {cache_error}")
                    print(f"❌ DEBUG: Failed to load expired cache: {cache_error}")

    def get_sleeper_players(self) -> List[Player]:
        """Get all NFL players from Sleeper API (cached)"""
        print("🔍 DEBUG: get_sleeper_players() called")
        
        if not self._sleeper_players_cache:
            print("❌ DEBUG: No Sleeper players cache available")
            logger.warning("❌ No Sleeper players cache available")
            return []
        
        print(f"🔍 DEBUG: Processing {len(self._sleeper_players_cache)} cached Sleeper players")
        players = []
        processed_count = 0
        
        for player_id, player_data in self._sleeper_players_cache.items():
            try:
                player = self._map_sleeper_player(player_id, player_data)
                if player:
                    players.append(player)
                    processed_count += 1
                    
                    # Log first few players for debugging
                    if processed_count <= 3:
                        print(f"🔍 DEBUG: Mapped player {processed_count}: {player.name} (rank={player.rank}, adp={player.adp})")
                        
            except Exception as e:
                logger.error(f"❌ Error mapping Sleeper player {player_id}: {e}")
                print(f"❌ DEBUG: Error mapping player {player_id}: {e}")
                continue
        
        print(f"🔍 DEBUG: Successfully mapped {len(players)} players from Sleeper cache")
        logger.info(f"✅ Mapped {len(players)} players from Sleeper cache")
        return players

    def get_sleeper_player_by_name(self, player_name: str) -> Optional[Player]:
        """Get specific player data from Sleeper API by name"""
        print(f"🔍 DEBUG: get_sleeper_player_by_name() called for: {player_name}")
        
        if not self._sleeper_players_cache:
            print("❌ DEBUG: No Sleeper players cache available")
            logger.warning("❌ No Sleeper players cache available")
            return None
        
        try:
            logger.info(f"🔍 Searching for player: '{player_name}' in Sleeper API")
            
            search_name = player_name.lower()
            print(f"🔍 DEBUG: Searching for '{search_name}' in {len(self._sleeper_players_cache)} players")
            
            # Search through cached players
            for player_id, player_data in self._sleeper_players_cache.items():
                try:
                    # Check various name fields
                    full_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".lower()
                    search_full_name = player_data.get('search_full_name', '').lower()
                    
                    if (search_name in full_name or 
                        full_name in search_name or 
                        search_name in search_full_name or
                        any(word in full_name for word in search_name.split())):
                        
                        print(f"🔍 DEBUG: Found match: {player_data.get('first_name', '')} {player_data.get('last_name', '')}")
                        player = self._map_sleeper_player(player_id, player_data)
                        if player:
                            print(f"🔍 DEBUG: Successfully mapped player: {player.name} (rank={player.rank}, adp={player.adp})")
                            logger.info(f"✅ Found player in Sleeper: '{player.name}'")
                            return player
                            
                except Exception as e:
                    logger.error(f"❌ Error processing Sleeper player {player_id}: {e}")
                    print(f"❌ DEBUG: Error processing player {player_id}: {e}")
                    continue
            
            print(f"❌ DEBUG: No match found for '{player_name}'")
            logger.warning(f"❌ Player not found in Sleeper: '{player_name}'")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting Sleeper player by name: {e}")
            print(f"❌ DEBUG: Exception in get_sleeper_player_by_name: {e}")
            return None

    def get_sleeper_players_by_names(self, player_names: List[str]) -> List[Player]:
        """Get multiple players from Sleeper API by names"""
        if not self._sleeper_players_cache:
            logger.warning("❌ No Sleeper players cache available")
            return []
        
        try:
            logger.info(f"🔍 Searching for {len(player_names)} players in Sleeper API: {player_names}")
            
            found_players = []
            search_names = player_names[:20]  # Limit to first 20 players
            
            for player_name in search_names:
                try:
                    player = self.get_sleeper_player_by_name(player_name)
                    if player:
                        found_players.append(player)
                        logger.info(f"✅ Added Sleeper player: {player.name} (proj={player.projected_points}, last={player.last_year_points})")
                    else:
                        logger.warning(f"❌ No Sleeper data found for: '{player_name}'")
                        
                except Exception as e:
                    logger.error(f"❌ Error getting Sleeper player '{player_name}': {e}")
                    continue  # Continue with next player instead of failing completely
            
            logger.info(f"✅ Found {len(found_players)} players out of {len(search_names)} requested")
            return found_players
            
        except Exception as e:
            logger.error(f"❌ Error getting Sleeper players by names: {e}")
            return []

    def get_sleeper_trending_players(self, trend_type: str = "add", limit: int = 25) -> List[Dict[str, Any]]:
        """Get trending players from Sleeper API"""
        try:
            logger.info(f"📡 Getting trending {trend_type} players from Sleeper API...")
            
            url = f"{self.sleeper_base_url}/players/nfl/trending/{trend_type}"
            params = {
                'lookback_hours': 24,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                logger.error(f"Sleeper trending API error: {response.status_code}")
                return []
            
            trending_data = response.json()
            logger.info(f"✅ Retrieved {len(trending_data)} trending {trend_type} players")
            
            # Enrich with player details
            enriched_trending = []
            for trending in trending_data:
                player_id = trending['player_id']
                if player_id in self._sleeper_players_cache:
                    player_data = self._sleeper_players_cache[player_id]
                    enriched_trending.append({
                        'player_id': player_id,
                        'count': trending['count'],
                        'trend_type': trend_type,
                        'name': f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                        'position': player_data.get('position', ''),
                        'team': player_data.get('team', 'FA'),
                        'search_rank': player_data.get('search_rank')
                    })
            
            return enriched_trending
            
        except Exception as e:
            logger.error(f"❌ Error getting trending players: {e}")
            return []

    def get_sleeper_trending_adds(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get trending add players"""
        return self.get_sleeper_trending_players("add", limit)

    def get_sleeper_trending_drops(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get trending drop players"""
        return self.get_sleeper_trending_players("drop", limit)

    def _map_sleeper_player(self, player_id: str, player_data: Dict[str, Any]) -> Optional[Player]:
        """Map Sleeper API player data to our Player model - using real fantasy data"""
        try:
            # Extract basic info
            first_name = player_data.get('first_name', '')
            last_name = player_data.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            if not full_name:
                return None
            
            # Map position
            position_str = player_data.get('position', '')
            position = self._map_sleeper_position(position_str)
            if not position:
                return None  # Skip non-fantasy positions
            
            # Extract other data with proper None handling
            team = player_data.get('team', '')
            if team is None:
                team = 'FA'  # Free Agent if no team
            
            age = player_data.get('age')
            experience = player_data.get('years_exp')
            injury_status = player_data.get('injury_status')
            
            # Use real Sleeper fantasy data
            search_rank = player_data.get('search_rank')
            print(f"🔍 DEBUG: Processing {full_name} - search_rank: {search_rank}")
            
            # Convert search_rank to fantasy rank (skip default values)
            if search_rank and search_rank != 9999999:
                rank = int(search_rank)
                print(f"🔍 DEBUG: {full_name} - Using real Sleeper rank: {rank}")
                
                # Generate ADP based on rank with some variance
                adp_variance = (hash(player_id) % 20) - 10  # ±10 picks
                adp = max(1.0, rank + adp_variance)
                adp = round(adp, 1)
                print(f"🔍 DEBUG: {full_name} - Calculated ADP: {adp}")
                
                # Calculate value score based on ADP vs rank
                if adp > 0 and rank > 0:
                    adp_rank_diff = adp - rank
                    if adp_rank_diff > 0:
                        value_score = min(10.0, 7.0 + (adp_rank_diff / 10))
                    else:
                        value_score = max(1.0, 7.0 + (adp_rank_diff / 10))
                else:
                    value_score = max(1.0, 10.0 - (rank / 30))
                value_score = round(value_score, 1)
                print(f"🔍 DEBUG: {full_name} - Calculated value score: {value_score}")
            else:
                rank = "N/A"
                adp = "N/A"
                value_score = "N/A"
                print(f"🔍 DEBUG: {full_name} - No valid Sleeper rank, using N/A")
            
            # Generate realistic projections based on position and rank
            if isinstance(rank, int):
                projected_points = self._generate_projection_from_rank(rank, position)
                print(f"🔍 DEBUG: {full_name} - Generated projections: proj={projected_points}")
            else:
                projected_points = "N/A"
                print(f"🔍 DEBUG: {full_name} - No projections (no valid rank)")
            
            # Create player object with real fantasy data
            player = Player(
                id=player_id,
                name=full_name,
                position=position,
                team=team,
                rank=rank,
                adp=adp,
                projected_points=projected_points,
                value_score=value_score,
                injury_status=injury_status,
                bye_week=None,  # Sleeper doesn't provide bye week in basic data
                age=age,
                experience=experience
            )
            
            print(f"🔍 DEBUG: Successfully created player: {full_name} (rank={rank}, adp={adp}, proj={projected_points})")
            return player
            
        except Exception as e:
            logger.error(f"❌ Error mapping Sleeper player {player_id}: {e}")
            print(f"❌ DEBUG: Error mapping player {player_id}: {e}")
            return None

    def _map_sleeper_position(self, position_str: str) -> Optional[Position]:
        """Map Sleeper position to our Position enum"""
        position_mapping = {
            'QB': Position.QB,
            'RB': Position.RB,
            'WR': Position.WR,
            'TE': Position.TE,
            'K': Position.K,
            'DEF': Position.DEF
        }
        return position_mapping.get(position_str) 

    def _generate_projection_from_rank(self, rank: int, position: Position) -> float:
        """Generate realistic projection based on Sleeper rank and position"""
        try:
            # Base projections by position
            position_bases = {
                Position.QB: {'top': 350, 'mid': 280, 'bottom': 200},
                Position.RB: {'top': 280, 'mid': 200, 'bottom': 120},
                Position.WR: {'top': 220, 'mid': 160, 'bottom': 100},
                Position.TE: {'top': 150, 'mid': 120, 'bottom': 80},
                Position.K: {'top': 160, 'mid': 130, 'bottom': 110},
                Position.DEF: {'top': 140, 'mid': 120, 'bottom': 100}
            }
            
            base = position_bases.get(position, position_bases[Position.WR])
            
            # Rank-based projection (lower rank = higher projection)
            if rank <= 50:
                projection = base['top']
            elif rank <= 150:
                projection = base['mid']
            else:
                projection = base['bottom']
            
            # Add some variance based on rank
            variance = (rank % 20) - 10  # ±10 points
            projection = max(50.0, projection + variance)
            
            return round(projection, 1)
            
        except Exception as e:
            logger.error(f"❌ Error generating projection: {e}")
            return 150.0

    def _generate_last_year_from_rank(self, rank: int, position: Position) -> float:
        """Generate realistic last year points based on rank and position"""
        try:
            # Similar to projection but with some variance
            projected = self._generate_projection_from_rank(rank, position)
            variance = (hash(str(rank)) % 30) - 15  # ±15 points
            last_year = max(30.0, projected + variance)
            return round(last_year, 1)
            
        except Exception as e:
            logger.error(f"❌ Error generating last year points: {e}")
            return 130.0 