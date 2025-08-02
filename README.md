# Fantasy Football Draft Assistant

An AI-powered fantasy football draft assistant that provides real-time player recommendations, draft strategy advice, and intelligent chat assistance during your Sleeper.com fantasy football drafts.

## Features

### Core Functionality
- **Real-time Player Recommendations**: Get intelligent player suggestions based on your current draft position, team needs, and available players
- **AI Chat Assistant**: Ask questions about players, strategies, or team composition and get instant responses
- **Position Analysis**: Track your team's positional needs and get priority recommendations
- **Value Analysis**: Identify players with good value relative to their ADP (Average Draft Position)
- **Risk Assessment**: Get insights on players with injury concerns or other risk factors

### Data Integration
- **Sleeper API Integration**: Real-time player data from Sleeper's fantasy football platform
- **Player Enrichment**: Enhanced player statistics with projected points, value scores, and rankings
- **Caching System**: Intelligent caching for faster responses and reduced API calls
- **Mock Data Support**: Fallback data for testing and development

### Chrome Extension
- **Seamless Integration**: Works directly within Sleeper.com draft pages
- **Real-time Data Scraping**: Automatically extracts draft board and team information
- **Interactive UI**: Click-to-select recommendations with visual feedback
- **Multi-tab Interface**: Recommendations, position analysis, AI chat, and debug tools

## Architecture

### Backend (FastAPI)
```
app/
├── main.py                 # FastAPI application entry point
├── api/                    # API endpoints
│   ├── chat.py            # Chat functionality
│   ├── players.py         # Player management
│   └── recommendations.py # Recommendation engine
├── models/                 # Data models
│   ├── chat.py           # Chat models
│   ├── draft.py          # Draft state models
│   └── player.py         # Player data models
└── services/              # Business logic
    ├── api_service.py     # External API integration
    ├── player_service.py  # Player data management
    └── rag_service.py     # RAG (Retrieval-Augmented Generation)
```

### Frontend (Chrome Extension)
```
├── manifest.json          # Extension configuration
├── popup.html            # Main extension UI
├── popup.js              # Extension logic
├── content.js            # Page scraping script
├── background.js         # Background service worker
├── styles.css            # UI styling
└── icons/               # Extension icons
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for development)
- Chrome browser
- Sleeper.com account

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fantasy-football-draft
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   echo "HOST=0.0.0.0" >> .env
   echo "PORT=8000" >> .env
   echo "DEBUG=True" >> .env
   ```

4. **Start the FastAPI server**
   ```bash
   python -m app.main
   ```

   The API will be available at `http://localhost:8000`

### Chrome Extension Setup

1. **Load the extension in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the project directory

2. **Navigate to Sleeper.com**
   - Go to `https://sleeper.com`
   - Start or join a draft
   - Click the extension icon to open the assistant

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Get AI chat responses
- `POST /api/chat/session/{session_id}` - Session-based chat
- `GET /api/chat/sessions` - List chat sessions
- `DELETE /api/chat/session/{session_id}` - Delete session
- `POST /api/chat/clear` - Clear chat cache

### Player Endpoints
- `GET /api/players` - List all players
- `GET /api/players/{player_id}` - Get specific player
- `GET /api/players/search/{name}` - Search players by name
- `GET /api/players/{player_id}/analysis` - Get player analysis
- `POST /api/players/sync/sleeper` - Sync with Sleeper API
- `POST /api/players/enrich` - Enrich player data

### Recommendation Endpoints
- `POST /api/recommendations` - Get player recommendations
- `GET /api/recommendations/position/{position}` - Position-specific recommendations
- `GET /api/recommendations/value` - Value-based recommendations
- `GET /api/recommendations/scarcity` - Positional scarcity analysis
- `GET /api/recommendations/risk` - Risk assessment

## AI Features

### RAG Service
The application uses a Retrieval-Augmented Generation (RAG) system with two modes:

1. **Groq LLM Mode** (Preferred)
   - Uses Groq's fast LLM API
   - Requires `GROQ_API_KEY` environment variable
   - Provides intelligent, context-aware responses

2. **Rule-based Fallback**
   - Works without API keys
   - Provides basic recommendations based on player rankings
   - Ensures functionality even without external AI services

### Chat Capabilities
- **Draft Strategy Questions**: "What's the best strategy for round 3?"
- **Player Analysis**: "Should I draft Christian McCaffrey?"
- **Positional Advice**: "Do I need another RB?"
- **Value Questions**: "Who's the best value pick right now?"

## Data Models

### Player Model
```python
class Player(BaseModel):
    id: str
    name: str
    position: Position  # QB, RB, WR, TE, K, DEF
    team: str
    rank: Optional[int]
    adp: Optional[float]  # Average Draft Position
    projected_points: Optional[float]
    value_score: Optional[float]
    injury_status: Optional[str]
    bye_week: Optional[int]
    age: Optional[int]
    experience: Optional[int]
```

### Recommendation Model
```python
class RecommendationResponse(BaseModel):
    primary_recommendation: Recommendation
    alternative_recommendations: List[Recommendation]
    strategy_notes: str
    next_picks_suggestion: List[str]
```

## Configuration

### Environment Variables
- `GROQ_API_KEY`: API key for Groq LLM service
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: False)

### Extension Settings
The Chrome extension automatically:
- Injects content scripts on Sleeper.com pages
- Scrapes draft board data every 10 seconds
- Caches responses for 5 minutes
- Manages persistent storage for chat history

## Development

### Running Tests
```bash
# Run backend tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

### Debugging
- Backend logs are available in the console
- Extension logs are available in Chrome DevTools
- Content script logs appear in the page console
- Background script logs appear in extension DevTools

### Data Sources
- **Sleeper API**: Primary source for player data
- **Mock Data**: Generated for testing and fallback
- **Cache**: Redis-like in-memory caching system

## Usage

### During a Draft
1. **Open the extension** while on a Sleeper draft page
2. **View recommendations** in the main tab
3. **Check position analysis** to see team needs
4. **Ask the AI** for strategy advice
5. **Click recommendations** to select players

### Extension Tabs
- **Recommendations**: Primary and alternative picks
- **Positions**: Team composition analysis
- **AI Chat**: Interactive draft assistant
- **Debug**: Draft board data and cache stats

## Security

- CORS enabled for development
- API key stored in environment variables
- No sensitive data logged
- Cache expiration prevents stale data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Sleeper.com** for providing the fantasy football platform
- **Groq** for fast LLM inference
- **FastAPI** for the robust backend framework
- **Chrome Extensions API** for browser integration

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the code comments

---

**Happy Drafting!** 