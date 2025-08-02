# Fantasy Football Draft Assistant Backend

A FastAPI-powered backend for intelligent fantasy football draft recommendations using RAG (Retrieval-Augmented Generation) with LLMs.

## 🚀 Features

- **RAG-powered Recommendations**: AI-driven player recommendations using LangChain and OpenAI
- **Real-time Chat**: Interactive chat system for draft strategy questions
- **Player Analysis**: Detailed player analysis with strengths, weaknesses, and risk assessment
- **Positional Scarcity Analysis**: Smart analysis of position availability
- **Value Opportunity Detection**: Find undervalued players based on ADP vs rank
- **Vector Database**: ChromaDB for efficient player data storage and retrieval
- **RESTful API**: Complete API for Chrome extension integration

## 🏗️ Architecture

```
fantasy-football-backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models/                 # Pydantic data models
│   │   ├── player.py          # Player and recommendation models
│   │   ├── chat.py            # Chat message models
│   │   └── draft.py           # Draft context models
│   ├── services/              # Business logic
│   │   ├── rag_service.py     # RAG pipeline with LLM
│   │   └── player_service.py  # Player data management
│   └── api/                   # API routes
│       ├── chat.py            # Chat endpoints
│       ├── recommendations.py # Recommendation endpoints
│       └── players.py         # Player management endpoints
├── data/                      # Data storage
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- Chrome extension (for frontend)
- Optional: Ollama (for local LLM) or Hugging Face API token (for cloud LLM)

### Installation

1. **Clone and navigate to the backend directory:**
   ```bash
   cd fantasy-football-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   Create a `.env` file in the root directory:
   ```env
   # Optional: Hugging Face API token (free tier: 30k requests/month)
   HUGGINGFACE_API_TOKEN=your_huggingface_token_here
   
   # Server configuration
   HOST=0.0.0.0
   PORT=8000
   DEBUG=True
   ```
   
   **LLM Options:**
   - **Ollama (Recommended)**: Install from https://ollama.ai and run `ollama pull llama2`
   - **Hugging Face API**: Get free token from https://huggingface.co/settings/tokens
   - **Rule-based**: Works without any LLM (fallback mode)

5. **Run the server:**
   ```bash
   python -m app.main
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Health Check
```bash
GET /
GET /health
```

### Chat Endpoints

#### Chat with RAG
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Who should I draft in round 3?",
  "draft_context": {
    "current_round": 3,
    "current_pick": 25,
    "total_teams": 12
  },
  "user_team": {
    "players": [...],
    "position_counts": {"RB": 2, "WR": 1}
  }
}
```

#### Chat with Session
```bash
POST /api/chat/session/{session_id}
```

### Recommendation Endpoints

#### Get Player Recommendations
```bash
POST /api/recommendations
Content-Type: application/json

{
  "available_players": [...],
  "user_team": {...},
  "draft_context": {...},
  "preferences": {...}
}
```

#### Get Position Recommendations
```bash
GET /api/recommendations/position/{position}?limit=10
```

#### Get Value Opportunities
```bash
GET /api/recommendations/value
```

#### Get Positional Scarcity
```bash
GET /api/recommendations/scarcity
```

### Player Endpoints

#### Get All Players
```bash
GET /api/players?position=RB&limit=20
```

#### Get Player by ID
```bash
GET /api/players/{player_id}
```

#### Get Player Analysis
```bash
GET /api/players/{player_id}/analysis
```

#### Search Players
```bash
GET /api/players/search/{name}?limit=10
```

#### Create Player
```bash
POST /api/players
Content-Type: application/json

{
  "id": "player_1",
  "name": "Christian McCaffrey",
  "position": "RB",
  "team": "SF",
  "rank": 1,
  "adp": 1.5,
  "projected_points": 250.0
}
```

## 🔧 Integration with Chrome Extension

### Update your extension's popup.js:

```javascript
// Replace simple recommendations with API calls
async function loadRecommendations() {
    try {
        const response = await fetch('http://localhost:8000/api/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                available_players: draftData.availablePlayers,
                user_team: userTeamData,
                draft_context: {
                    current_round: draftData.draftRound,
                    current_pick: draftData.currentPick,
                    total_teams: 12
                }
            })
        });
        
        const recommendations = await response.json();
        displayRecommendations(recommendations);
    } catch (error) {
        console.error('Error loading recommendations:', error);
        // Fallback to simple recommendations
    }
}

// Replace simple chat with API calls
async function sendChatMessage() {
    const message = document.getElementById('chat-input').value;
    
    try {
        const response = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                draft_context: currentDraftData,
                user_team: userTeamData
            })
        });
        
        const chatResponse = await response.json();
        displayChatResponse(chatResponse.response);
    } catch (error) {
        console.error('Error sending chat message:', error);
    }
}
```

## 🧠 RAG Pipeline

The RAG (Retrieval-Augmented Generation) system works as follows:

1. **Data Ingestion**: Player data is stored with embeddings using SentenceTransformers
2. **Query Processing**: User questions are converted to embeddings
3. **Retrieval**: Relevant player data is retrieved using similarity search
4. **Generation**: Free LLM generates responses using retrieved context
5. **Response**: Structured recommendations are returned to the user

### Key Components:

- **SentenceTransformers**: Free embeddings for semantic search
- **Ollama**: Local LLM (Llama 2) for intelligent responses
- **Hugging Face API**: Cloud LLM alternative (free tier)
- **Rule-based Fallback**: Works without any LLM

## 📊 Data Models

### Player Model
```python
class Player(BaseModel):
    id: str
    name: str
    position: Position
    team: str
    rank: Optional[int]
    adp: Optional[float]
    projected_points: Optional[float]
    last_year_points: Optional[float]
    value_score: Optional[float]
    injury_status: Optional[str]
    bye_week: Optional[int]
    age: Optional[int]
    experience: Optional[int]
```

### Recommendation Model
```python
class Recommendation(BaseModel):
    player: Player
    reasoning: str
    confidence_score: float
    alternatives: List[Player]
    risk_assessment: str
```

## 🚀 Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### Testing
```bash
# Run tests (when implemented)
pytest

# Test specific endpoint
curl -X GET "http://localhost:8000/health"
```

## 🔒 Security Considerations

- Store API keys securely in environment variables
- Implement rate limiting for production
- Add authentication for user-specific data
- Validate all input data
- Use HTTPS in production

## 📈 Performance Optimization

- Cache frequently accessed player data
- Use connection pooling for database
- Implement pagination for large datasets
- Optimize vector database queries
- Use async operations where possible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Ensure all environment variables are set correctly
4. Verify the Chrome extension is properly configured

---

**Next Steps:**
1. Set up your OpenAI API key
2. Run the backend server
3. Update your Chrome extension to use the new API endpoints
4. Test the RAG-powered recommendations! 

## Populating Player Data with Real Sleeper API Data

The system now automatically enriches player data with real information from the Sleeper API. Here's how it works:

### **Automatic Enrichment**
- **Real-time**: When you request recommendations, the system automatically fetches real player data from Sleeper API
- **Smart Caching**: Follows Sleeper's best practices by caching the full player list for 24 hours (5MB response)
- **Efficient**: Only calls the API once per day, then searches cached data for specific players

### **What Data We Get**
From the Sleeper API, we fetch:
- **Player Information**: Name, position, team, age, experience
- **Rankings**: Search rank, ADP (when available)
- **Status**: Active/inactive, injury status
- **Generated Stats**: Realistic fantasy points based on rank and position

### **Stats Generation**
Since Sleeper API doesn't provide fantasy football stats, we generate realistic ones based on:
- **Player Rank**: Higher rank = better projected points
- **Position**: Different stat ranges for QB, RB, WR, TE, K, DEF
- **Tier System**: 
  - Top tier (rank 1-12): Elite players
  - Mid tier (rank 13-48): Solid starters
  - Low tier (rank 49+): Bench/depth players

### **Value Score Calculation**
- **ADP vs Rank**: If ADP is higher than rank = good value
- **Rank-based**: If no ADP, uses rank to determine value
- **Rounded**: All value scores rounded to 1 decimal place

### **Manual Testing**
You can test the Sleeper integration:

```bash
# Test getting a specific player
python test_player_stats.py

# Test the full debug suite
python debug_sleeper.py

# Test via API endpoints
curl http://localhost:8000/api/players/sleeper/Christian%20McCaffrey
```

### **API Endpoints**
- `GET /api/players/sleeper/{player_name}` - Get specific player data
- `POST /api/players/enrich-sleeper` - Enrich multiple players
- `POST /api/recommendations` - Automatic enrichment during recommendations

### **Best Practices Followed**
✅ **Sleeper API Guidelines**:
- Call `/players/nfl` endpoint sparingly (once per day max)
- Cache the 5MB response for 24 hours
- Use player IDs for efficient lookups
- Don't make repeated API calls for the same data

The system now provides **real player data from Sleeper API** with **realistic fantasy football stats** that will show up in your recommendations instead of "N/A"! 