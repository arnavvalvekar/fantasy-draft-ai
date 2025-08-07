import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import Groq
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.models.player import Player, Recommendation, RecommendationResponse
from app.models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for fantasy football recommendations and chat using LangChain and Groq LLM"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Initialize embeddings using HuggingFace through LangChain
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'}
            )
            logger.info("HuggingFace embeddings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            self.embeddings = None
        
        # Initialize vector store
        self.vectorstore = FAISS.from_texts(
            ["Initial empty store"], 
            self.embeddings
        )
        
        # LLM configuration
        self.llm_type = self._detect_llm()
        
        # Initialize LangChain components
        self.llm = None
        if self.llm_type == "groq":
            try:
                callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
                self.llm = Groq(
                    api_key=os.environ["GROQ_API_KEY"],
                    model_name="llama3-8b-8192",
                    callback_manager=callback_manager,
                    temperature=0.7
                )
                logger.info("Groq LLM initialized successfully")
            except KeyError:
                logger.warning("GROQ_API_KEY not found, falling back to rule-based responses")
                self.llm_type = "rule_based"
            except Exception as e:
                logger.error(f"Error initializing Groq LLM: {e}")
                self.llm_type = "rule_based"
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Initialize chains
        self.qa_chain = self._create_qa_chain() if self.llm else None
        self.chat_chain = self._create_chat_chain() if self.llm else None
        
        # Caching system
        self.recommendation_cache = {}
        self.chat_cache = {}
        self.player_cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def _detect_llm(self):
        """Detect available LLM options"""
        # Try Groq first (preferred)
        if os.getenv("GROQ_API_KEY"):
            logger.info("Groq API key found - using Groq LLM")
            return "groq"
        
        logger.info("No Groq API key found - using rule-based responses")
        return "rule_based"

    def _get_cache_key(self, available_players: List[Player], user_team: Dict[str, Any], draft_context: Dict[str, Any]) -> str:
        """Generate cache key for recommendations"""
        player_names = [p.name for p in available_players[:5]]  # Top 5 players
        team_players = [p.get('name', '') for p in user_team.get('players', [])]
        context = f"{draft_context.get('current_round', '')}-{draft_context.get('current_pick', '')}"
        
        return f"{'-'.join(player_names)}:{'-'.join(team_players)}:{context}"
    
    def _get_chat_cache_key(self, request: ChatRequest) -> str:
        """Generate cache key for chat requests"""
        # Create a hash of the message and draft context
        message_hash = hash(request.message.lower().strip())
        context_hash = hash(str(request.draft_context))
        
        return f"chat:{message_hash}:{context_hash}"

    def _is_cache_valid(self, cache_entry: tuple) -> bool:
        """Check if cache entry is still valid"""
        timestamp, _ = cache_entry
        return datetime.now() - timestamp < timedelta(seconds=self.cache_duration)

    def _create_qa_chain(self):
        """Create chain for player recommendations"""
        if not self.llm:
            return None
            
        recommendation_prompt = PromptTemplate(
            template="""You are a fantasy football draft expert assistant with access to real player data.
            Given the following draft context and available players, recommend the best next pick.
            
            Draft Context: {context}
            Available Players: {players}
            User Team: {team}
            
            Analyze the data and provide recommendations in this JSON format:
            {
                "primary_recommendation": {
                    "player_name": "string",
                    "reasoning": "string",
                    "confidence_score": float
                },
                "alternatives": [
                    {
                        "player_name": "string",
                        "reasoning": "string",
                        "confidence_score": float
                    }
                ],
                "strategy_notes": "string"
            }
            """,
            input_variables=["context", "players", "team"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(),
            chain_type_kwargs={
                "prompt": recommendation_prompt
            }
        )
        
    def _create_chat_chain(self):
        """Create chain for interactive chat"""
        if not self.llm:
            return None
            
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory,
            return_source_documents=True
        )
        
    def get_recommendations(self, 
                          available_players: List[Player],
                          user_team: Dict[str, Any],
                          draft_context: Dict[str, Any]) -> RecommendationResponse:
        """Get player recommendations using LangChain QA chain or rule-based fallback"""
        
        # Check cache first
        cache_key = self._get_cache_key(available_players, user_team, draft_context)
        logger.info(f"Generated cache key: {cache_key[:100]}...")
        logger.info(f"Current cache size: {len(self.recommendation_cache)}")
        
        if cache_key in self.recommendation_cache:
            cache_entry = self.recommendation_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.info("✅ Cache hit! Returning cached recommendation")
                return cache_entry[1]
            else:
                logger.info("⏰ Cache entry expired, removing...")
                del self.recommendation_cache[cache_key]
        else:
            logger.info("❌ Cache miss - generating new recommendation")
        
        # Update vector store with current player data
        self._update_vector_store(available_players)
        
        # Get recommendations using LangChain if available
        if self.qa_chain:
            try:
                # Format input for the chain
                query = {
                    "context": str(draft_context),
                    "players": str([p.dict() for p in available_players[:10]]),
                    "team": str(user_team)
                }
                
                # Get recommendation from chain
                result = self.qa_chain(query)
                response = self._parse_recommendation_response(result, available_players)
            except Exception as e:
                logger.error(f"Error getting recommendations from LangChain: {e}")
                response = self._rule_based_recommendations(available_players, user_team, draft_context)
        else:
            response = self._rule_based_recommendations(available_players, user_team, draft_context)
        
        # Cache the response
        self.recommendation_cache[cache_key] = (datetime.now(), response)
        logger.info(f"💾 Cached new recommendation for key: {cache_key[:50]}...")
        logger.info(f"Updated cache size: {len(self.recommendation_cache)}")
        
        return response

    def _update_vector_store(self, players: List[Player]):
        """Update vector store with current player data"""
        if not players:
            return
            
        # Convert players to documents
        documents = []
        for player in players:
            content = (
                f"{player.name} ({player.position}, {player.team})\n"
                f"Rank: {player.rank}, Projected Points: {player.projected_points}\n"
                f"Value Score: {player.value_score}, ADP: {player.adp}\n"
                f"Status: {player.injury_status or 'Healthy'}"
            )
            documents.append(Document(
                page_content=content,
                metadata=player.dict()
            ))
        
        # Update vector store
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        logger.info(f"Updated vector store with {len(documents)} player documents")
    
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Get chat response using LangChain conversation chain or fallback"""
        
        # Check cache first
        cache_key = self._get_chat_cache_key(request)
        logger.info(f"Generated chat cache key: {cache_key[:50]}...")
        logger.info(f"Current chat cache size: {len(self.chat_cache)}")
        
        if cache_key in self.chat_cache:
            cache_entry = self.chat_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.info("✅ Chat cache hit! Returning cached response")
                return cache_entry[1]
            else:
                logger.info("⏰ Chat cache entry expired, removing...")
                del self.chat_cache[cache_key]
        else:
            logger.info("❌ Chat cache miss - generating new response")
        
        # Generate response using LangChain if available
        if self.chat_chain:
            try:
                # Format the chat context
                context = f"Draft Context: {request.draft_context}\n"
                
                # Get response from conversation chain
                result = self.chat_chain({
                    "question": request.message,
                    "chat_history": self.memory.chat_memory.messages,
                    "context": context
                })
                
                response = ChatResponse(
                    response=result["answer"],
                    confidence=0.9 if result.get("source_documents") else 0.7
                )
            except Exception as e:
                logger.error(f"Error getting chat response from LangChain: {e}")
                response = self._rule_based_chat(request)
        else:
            response = self._rule_based_chat(request)
        
        # Cache the response
        self.chat_cache[cache_key] = (datetime.now(), response)
        logger.info(f"💾 Cached new chat response for key: {cache_key[:50]}...")
        logger.info(f"Updated chat cache size: {len(self.chat_cache)}")
        
        return response

    def clear_cache(self):
        """Clear all caches"""
        self.recommendation_cache.clear()
        self.chat_cache.clear()
        self.player_cache.clear()
        logger.info("All caches cleared")

    def clear_chat_cache(self):
        """Clear only the chat cache"""
        self.chat_cache.clear()
        logger.info("Chat cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "recommendation_cache_size": len(self.recommendation_cache),
            "chat_cache_size": len(self.chat_cache),
            "player_cache_size": len(self.player_cache),
            "cache_duration_seconds": self.cache_duration
        }
    
    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance (for testing)"""
        cls._instance = None
        cls._initialized = False



    # --- Groq LLM ---
    def _groq_recommendations(self, available_players, user_team, draft_context):
        """Get recommendations from Groq LLM"""
        if not self.groq_client:
            logger.warning("Groq client not available, falling back to rule-based recommendations")
            return self._rule_based_recommendations(available_players, user_team, draft_context)
            
        prompt = self._build_recommendation_prompt(available_players, user_team, draft_context)
        logger.info(f"Groq recommendation prompt: {prompt[:200]}...")
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",  # Fast and reliable model
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.7,
            )
            text = completion.choices[0].message.content
            logger.info(f"Groq recommendation response: {text[:200]}...")
            return self._parse_llm_recommendations(text, available_players)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            logger.info("Falling back to rule-based recommendations")
            return self._rule_based_recommendations(available_players, user_team, draft_context)

    # --- Rule-based fallback ---
    def _rule_based_recommendations(self, available_players, user_team, draft_context):
        """Rule-based recommendations when LLM is not available"""
        logger.info(f"🤖 Using rule-based recommendations for {len(available_players)} players")
        
        if not available_players:
            return RecommendationResponse(
                primary_recommendation=Recommendation(
                    player=Player(
                        id="", 
                        name="No players available", 
                        position="QB", 
                        team="",
                        rank=0,
                        projected_points=0.0,
                        value_score=0.0
                    ),
                    reasoning="No players available for recommendation",
                    confidence_score=0.0
                ),
                alternative_recommendations=[],
                strategy_notes="No players available",
                next_picks_suggestion=[]
            )
        
        # Use the actual enriched players instead of fallback data
        # Sort players by rank (lower is better) and projected points
        sorted_players = sorted(available_players, key=lambda p: (p.rank or float('inf'), -(p.projected_points or 0)))
        
        if not sorted_players:
            return RecommendationResponse(
                primary_recommendation=Recommendation(
                    player=Player(
                        id="", 
                        name="No valid players", 
                        position="QB", 
                        team="",
                        rank=0,
                        projected_points=0.0,
                        value_score=0.0
                    ),
                    reasoning="No valid players available for recommendation",
                    confidence_score=0.0
                ),
                alternative_recommendations=[],
                strategy_notes="No valid players",
                next_picks_suggestion=[]
            )
        
        # Use the top player as primary recommendation
        primary_player = sorted_players[0]
        
        primary_rec = Recommendation(
            player=primary_player,
            reasoning=f"{primary_player.name} is the highest ranked available player with {primary_player.projected_points} projected points",
            confidence_score=0.6
        )
        
        # Use the next 2 players as alternatives
        alternatives = []
        for i, player in enumerate(sorted_players[1:3]):
            alternatives.append(Recommendation(
                player=player,
                reasoning=f"Alternative option: {player.name} with {player.projected_points} projected points",
                confidence_score=0.5 - (i * 0.1)
            ))
        
        return RecommendationResponse(
            primary_recommendation=primary_rec,
            alternative_recommendations=alternatives,
            strategy_notes="Using rule-based recommendations with actual player data",
            next_picks_suggestion=["Consider positional needs", "Check for value picks"]
        )

    def _rule_based_chat(self, request):
        message = request.message.lower()
        if "recommend" in message or "who should" in message:
            response = "Based on your current draft position, I recommend taking the best available player that fits your team's needs. Consider positional scarcity and value."
        elif "strategy" in message:
            response = "Focus on building a balanced team. In early rounds, take the best player available. In middle rounds, address positional needs. In late rounds, look for value picks."
        elif "position" in message:
            response = "Consider your team's current position distribution and the scarcity of positions in the available player pool."
        else:
            response = "I'm here to help with your fantasy football draft! Ask me about player recommendations, draft strategy, or positional analysis."
        return ChatResponse(
            response=response,
            confidence=0.6
        )

    def _groq_chat(self, request: ChatRequest) -> ChatResponse:
        if not self.groq_client:
            logger.warning("Groq client not available, falling back to rule-based chat")
            return self._rule_based_chat(request)
            
        prompt = self._build_chat_prompt(request)
        logger.info(f"Groq prompt: {prompt[:200]}...")
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",  # Fast and reliable model
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            text = completion.choices[0].message.content
            logger.info(f"Groq response: {text[:200]}...")
            
            # Process the response: trim whitespace and convert asterisks to bold
            logger.info(f"🔍 Original LLM response: '{text[:100]}'")
            logger.info(f"🔍 Original response length: {len(text)}")
            logger.info(f"🔍 Original response starts with: '{text[:50]}'")
            
            processed_text = self._process_chat_response(text)
            logger.info(f"🔍 Processed text: '{processed_text[:100]}'")
            logger.info(f"🔍 Processed text length: {len(processed_text)}")
            logger.info(f"🔍 Processed text starts with: '{processed_text[:50]}'")
            
            return ChatResponse(
                response=processed_text,
                confidence=0.9
            )
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            logger.info("Falling back to rule-based chat")
            return self._rule_based_chat(request)

    # --- Prompt builders and parsers ---
    def _build_recommendation_prompt(self, available_players, user_team, draft_context):
        player_lines = [
            f"{p.name} ({p.position}, {p.team}, Rank: {p.rank}, Proj: {p.projected_points}, Value: {p.value_score})"
            for p in available_players[:10]
        ]
        prompt = (
            "You are a fantasy football draft expert assistant with access to real ESPN fantasy data. "
            "Given the following draft context, user team, and available players with real ESPN projections, recommend the best next pick. "
            "Use the real fantasy projections and value scores to make data-driven recommendations. "
            "Explain your reasoning in detail and format your response as JSON.\n"
            f"Draft Context: Round {draft_context.get('current_round', 'N/A')}, Pick {draft_context.get('current_pick', 'N/A')}, Total Teams: {draft_context.get('total_teams', 'N/A')}\n"
            f"User Team: Players: {[p.get('name', '') for p in user_team.get('players', [])]}, Position Counts: {user_team.get('position_counts', {})}\n"
            f"Available Players (with ESPN projections): {', '.join(player_lines)}\n"
            "Please recommend the best player using real ESPN fantasy projections and value analysis. Format your response as JSON: {\n"
            "  \"primary_recommendation\": {\n"
            "    \"player_name\": \"string\",\n"
            "    \"reasoning\": \"string (include ESPN projections and value analysis)\",\n"
            "    \"confidence_score\": 0.0-1.0\n"
            "  },\n"
            "  \"alternatives\": [\n"
            "    {\n"
            "      \"player_name\": \"string\",\n"
            "      \"reasoning\": \"string (include ESPN projections and value analysis)\",\n"
            "      \"confidence_score\": 0.0-1.0\n"
            "    }\n"
            "  ],\n"
            "  \"strategy_notes\": \"string (include ESPN data insights)\"\n"
            "}\n"
        )
        return prompt

    def _build_chat_prompt(self, request):
        prompt = (
            "You are a fantasy football draft expert assistant with access to real ESPN fantasy data and projections. "
            "Provide clear, concise, and actionable advice based on real fantasy football statistics. "
            f"User Question: {request.message}\n"
            f"Draft Context: {request.draft_context}\n"
            "Keep your response under 150 words. Use bullet points and short paragraphs for clarity. "
            "Start your response immediately with the first word. No leading newlines or spaces. "
            "Use • for bullet points and **text** for bold formatting. "
            "When discussing players, reference ESPN projections and value analysis when available."
        )
        return prompt

    def _parse_recommendation_response(self, result, available_players):
        """Parse LangChain recommendation response"""
        try:
            # Extract JSON from response
            response_text = result.get('result', '') or result.get('answer', '')
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)
            
            # Find primary recommendation player
            primary_player = self._find_player_by_name(
                data["primary_recommendation"]["player_name"], 
                available_players
            )
            
            if not primary_player:
                logger.warning("Primary recommended player not found in available players")
                return self._rule_based_recommendations(available_players, {}, {})
                
            # Create primary recommendation
            primary_rec = Recommendation(
                player=primary_player,
                reasoning=data["primary_recommendation"]["reasoning"],
                confidence_score=data["primary_recommendation"]["confidence_score"]
            )
            
            # Process alternative recommendations
            alternatives = []
            for alt in data.get("alternatives", []):
                alt_player = self._find_player_by_name(alt["player_name"], available_players)
                if alt_player:
                    alternatives.append(Recommendation(
                        player=alt_player,
                        reasoning=alt["reasoning"],
                        confidence_score=alt["confidence_score"]
                    ))
                    
            # Create response
            return RecommendationResponse(
                primary_recommendation=primary_rec,
                alternative_recommendations=alternatives,
                strategy_notes=data.get("strategy_notes", ""),
                next_picks_suggestion=[
                    "Consider positional balance",
                    "Look for value picks",
                    "Monitor injury status"
                ]
            )
        except Exception as e:
            logger.error(f"Error parsing LangChain recommendations: {e}")
            return self._rule_based_recommendations(available_players, {}, {})

    def _process_chat_response(self, text):
        """Process chat response - return as-is for now"""
        return text

    def _find_player_by_name(self, name, players):
        for player in players:
            if player.name.lower() == name.lower():
                return player
        return None 
    