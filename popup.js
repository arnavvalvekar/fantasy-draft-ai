// Popup script for Fantasy Football Draft Helper
console.log('Fantasy Football Draft Helper: Popup script loaded');

// Cache management functions
function generateCacheKey(type, data) {
    // Create a simple hash of the data for cache key
    const dataStr = JSON.stringify(data);
    let hash = 0;
    for (let i = 0; i < dataStr.length; i++) {
        const char = dataStr.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return `${type}:${Math.abs(hash)}`;
}

function cacheRecommendation(key, data) {
    try {
        chrome.runtime.sendMessage({
            type: 'CACHE_RECOMMENDATION',
            key: key,
            data: data
        }, (response) => {
            if (response && response.success) {
                console.log('💾 Cached recommendation with key:', key.substring(0, 50) + '...');
            }
        });
    } catch (err) {
        console.error('❌ Error sending CACHE_RECOMMENDATION message:', err);
    }
}

function getCachedRecommendation(key) {
    return new Promise((resolve) => {
        try {
            chrome.runtime.sendMessage({
                type: 'GET_CACHED_RECOMMENDATION',
                key: key
            }, (response) => {
                resolve(response);
            });
        } catch (err) {
            console.error('❌ Error sending GET_CACHED_RECOMMENDATION message:', err);
            resolve(null);
        }
    });
}

function cacheChat(key, data) {
    console.log('📤 Sending CACHE_CHAT message to background script');
    console.log('🔑 Cache key:', key.substring(0, 50) + '...');
    console.log('📦 Cache data:', data);
    
    try {
        chrome.runtime.sendMessage({
            type: 'CACHE_CHAT',
            key: key,
            data: data
        }, (response) => {
            console.log('📥 Received response from background script:', response);
            if (response && response.success) {
                console.log('✅ Chat cached successfully with key:', key.substring(0, 50) + '...');
            } else {
                console.log('❌ Failed to cache chat response');
            }
        });
    } catch (err) {
        console.error('❌ Error sending CACHE_CHAT message:', err);
    }
}

function getCachedChat(key) {
    console.log('📤 Sending GET_CACHED_CHAT message to background script');
    console.log('🔑 Looking for cache key:', key.substring(0, 50) + '...');
    
    return new Promise((resolve) => {
        try {
            chrome.runtime.sendMessage({
                type: 'GET_CACHED_CHAT',
                key: key
            }, (response) => {
                console.log('📥 Received cached chat response:', response ? 'found' : 'not found');
                resolve(response);
            });
        } catch (err) {
            console.error('❌ Error sending GET_CACHED_CHAT message:', err);
            resolve(null);
        }
    });
}

function getCacheStats() {
    return new Promise((resolve) => {
        try {
            chrome.runtime.sendMessage({
                type: 'GET_CACHE_STATS'
            }, (response) => {
                resolve(response);
            });
        } catch (err) {
            console.error('❌ Error sending GET_CACHE_STATS message:', err);
            resolve(null);
        }
    });
}

function updateCacheStats(stats) {
    const cacheStatsElement = document.getElementById('cache-stats');
    if (cacheStatsElement && stats) {
        cacheStatsElement.innerHTML = `
            <div class="stat-item">
                <span class="label">Recommendations:</span>
                <span class="value">${stats.recommendations || 0}</span>
            </div>
            <div class="stat-item">
                <span class="label">Chat Messages:</span>
                <span class="value">${stats.chat || 0}</span>
            </div>
            <div class="stat-item">
                <span class="label">Last Update:</span>
                <span class="value">${stats.lastUpdate ? new Date(stats.lastUpdate).toLocaleTimeString() : 'Never'}</span>
            </div>
        `;
    }
}

function clearAllCache() {
    try {
        chrome.runtime.sendMessage({
            type: 'CLEAR_CACHE'
        }, (response) => {
            if (response && response.success) {
                console.log('🗑️ Cache cleared successfully');
                // Refresh cache stats
                getCacheStats().then(stats => {
                    updateCacheStats(stats);
                });
            }
        });
    } catch (err) {
        console.error('❌ Error sending CLEAR_CACHE message:', err);
    }
}

function debugCache() {
    try {
        chrome.runtime.sendMessage({
            type: 'DEBUG_CACHE'
        }, (response) => {
            if (response) {
                console.log('📊 DEBUG: Cache contents received:');
                console.log('📦 Recommendations:', response.recommendations);
                console.log('📦 Chat:', response.chat);
                console.log('🔑 Keys:', response.keys);
            }
        });
    } catch (err) {
        console.error('❌ Error sending DEBUG_CACHE message:', err);
    }
}

// Function to clear expired chat messages
function clearExpiredChatMessages() {
    console.log('🧹 Clearing expired chat messages...');
    chrome.runtime.sendMessage({
        type: 'CLEAR_EXPIRED_CHAT'
    }, (response) => {
        if (response && response.cleared) {
            console.log(`✅ Cleared ${response.count} expired chat messages`);
        }
    });
}

// Function to load cached chat messages
function loadCachedChatMessages() {
    console.log('🔄 Loading cached chat messages...');
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    // Clear existing messages except the initial AI message
    const initialMessage = chatMessages.querySelector('.ai-message');
    chatMessages.innerHTML = '';
    if (initialMessage) {
        chatMessages.appendChild(initialMessage);
    }
    
    // Get all cached chat messages and display them
    chrome.runtime.sendMessage({
        type: 'DEBUG_CACHE'
    }, (response) => {
        if (response && response.chat) {
            console.log('📦 Found cached chat messages:', Object.keys(response.chat).length);
            
            // Sort by timestamp to show in chronological order
            const sortedEntries = Object.entries(response.chat).sort((a, b) => a[1].timestamp - b[1].timestamp);
            
            sortedEntries.forEach(([key, entry]) => {
                if (entry.data) {
                    // Handle both old and new cache formats
                    const responseData = entry.data.aiResponse || entry.data;
                    const userMessage = entry.data.userMessage || '[Cached message]';
                    
                    if (responseData && responseData.response) {
                        console.log('📝 Displaying cached message:', responseData.response.substring(0, 50) + '...');
                        
                        // Add user message
                        const userMessageDiv = document.createElement('div');
                        userMessageDiv.className = 'message user-message';
                        userMessageDiv.innerHTML = `
                            <div class="message-content">
                                ${userMessage}
                            </div>
                        `;
                        chatMessages.appendChild(userMessageDiv);
                        
                        // Add AI response
                        const aiMessageDiv = document.createElement('div');
                        aiMessageDiv.className = 'message ai-message';
                        aiMessageDiv.innerHTML = `<div class="message-content">${convertMarkdownToHtml(cleanResponseText(responseData.response || 'No response from AI.'))}</div>`;
                        chatMessages.appendChild(aiMessageDiv);
                    }
                }
            });
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            console.log('✅ Loaded all cached chat messages');
        }
    });
}

// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Load data for the selected tab
            loadTabData(targetTab);
        });
    });
    
    // Refresh data button
    const refreshButton = document.getElementById('refresh-data');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshData();
        });
    }
    
    // Sync data button
    const syncButton = document.getElementById('sync-data');
    if (syncButton) {
        syncButton.addEventListener('click', function() {
            syncPlayerData();
        });
    }
    
    // Chat functionality
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    
    if (sendButton) {
        sendButton.addEventListener('click', sendChatMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    // Initial data load
    loadTabData('recommendations');
    
    // Log cache stats on startup
    getCacheStats().then(stats => {
        console.log('📊 Cache stats on startup:', stats);
        updateCacheStats(stats);
    }).catch(err => {
        console.error('❌ Error getting cache stats:', err);
    });
    
    // Don't clear chat messages on popup open - let them persist
    console.log('📊 Chat messages will persist across popup sessions');
    
    // Clear cache button
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', clearAllCache);
    }
    
    // Debug cache button
    const debugCacheBtn = document.getElementById('debug-cache-btn');
    if (debugCacheBtn) {
        debugCacheBtn.addEventListener('click', debugCache);
    }

    // Clear expired chat messages on popup open
    clearExpiredChatMessages();
});

// Smart name extraction function
function extractCleanPlayerName(rawName) {
    console.log('🧹 Cleaning player name:', rawName);
    
    if (!rawName) return '';
    
    // Common patterns for concatenated names
    const patterns = [
        // Pattern: "FirstName LastNamePOS TEAM" (e.g., "David MontgomeryRB DET")
        /^(.+?)(RB|QB|WR|TE|K|DEF)\s+([A-Z]{2,3})$/,
        // Pattern: "FirstName LastNamePOS" (e.g., "David MontgomeryRB")
        /^(.+?)(RB|QB|WR|TE|K|DEF)$/,
        // Pattern: "FirstName LastName TEAM" (e.g., "David Montgomery DET")
        /^(.+?)\s+([A-Z]{2,3})$/,
        // Pattern: "FirstName LastNamePOS TEAM" with multiple spaces
        /^(.+?)\s+(RB|QB|WR|TE|K|DEF)\s+([A-Z]{2,3})$/,
    ];
    
    for (const pattern of patterns) {
        const match = rawName.match(pattern);
        if (match) {
            const cleanName = match[1].trim();
            console.log('✅ Extracted clean name:', cleanName, 'from pattern:', pattern);
            return cleanName;
        }
    }
    
    // If no pattern matches, try to remove common suffixes
    let cleanName = rawName;
    
    // Remove position suffixes
    const positions = ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'];
    for (const pos of positions) {
        if (cleanName.endsWith(pos)) {
            cleanName = cleanName.slice(0, -pos.length).trim();
            console.log('✅ Removed position suffix:', pos);
        }
    }
    
    // Remove team abbreviations (2-3 letter codes)
    cleanName = cleanName.replace(/\s+[A-Z]{2,3}$/, '').trim();
    
    console.log('✅ Final cleaned name:', cleanName);
    return cleanName || rawName; // Fallback to original if cleaning fails
}

// Enhanced player mapping function
function mapToPlayerModel(player) {
    console.log('🗺️ Mapping player:', player);
    
    // Clean up player name using smart extraction
    const cleanName = extractCleanPlayerName(player.name);
    
    // Clean up team name
    let cleanTeam = player.team || '';
    if (cleanTeam.includes('_')) {
        cleanTeam = cleanTeam.split('_')[0];
    }
    
    // Remove position from team name if present
    const positions = ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'];
    for (const pos of positions) {
        cleanTeam = cleanTeam.replace(pos, '').trim();
    }
    
    const mappedPlayer = {
        id: (cleanName || '') + '_' + (player.position || '') + '_' + (cleanTeam || ''),
        name: cleanName || '',
        position: (player.position || 'RB'), // fallback to RB if missing
        team: cleanTeam || 'Unknown',
        rank: player.rank || null,
        adp: player.adp || null,
        projected_points: player.projected_points || null,
        value_score: player.value_score || null,
        injury_status: player.injury_status || null,
        bye_week: player.bye_week || null,
        age: player.age || null,
        experience: player.experience || null
    };
    
    console.log('✅ Mapped player:', mappedPlayer);
    return mappedPlayer;
}

// Helper: Map teamData to TeamRoster model
function mapToTeamRoster(teamData) {
    return {
        team_name: teamData && teamData.teamName ? teamData.teamName : 'My Team',
        players: (teamData && Array.isArray(teamData.players)) ? teamData.players.map(mapToPlayerModel) : [],
        position_counts: teamData && teamData.positionCounts ? teamData.positionCounts : {},
        total_points: teamData && teamData.totalPoints ? teamData.totalPoints : 0.0
    };
}

// Helper: Build DraftContext
function buildDraftContext(draftData, teamData) {
    // Parse current_pick and current_round as integers
    let currentPick = draftData.currentPick;
    if (typeof currentPick === 'string') {
        // Extract number from string like 'Pick 58'
        const match = currentPick.match(/\d+/);
        currentPick = match ? parseInt(match[0], 10) : 1;
    }
    let currentRound = draftData.draftRound;
    if (typeof currentRound === 'string') {
        const match = currentRound.match(/\d+/);
        currentRound = match ? parseInt(match[0], 10) : 1;
    }
    return {
        current_round: currentRound || 1,
        current_pick: currentPick || 1,
        total_teams: draftData.totalTeams || 12,
        user_team_position: 1, // You can improve this if you know the user's draft slot
        league_settings: {},
        scoring_format: 'PPR'
    };
}

// Function to load data for specific tabs
function loadTabData(tabName) {
    console.log('🔄 Loading data for tab:', tabName);
    
    switch(tabName) {
        case 'recommendations':
            loadRecommendations();
            break;
        case 'positions':
            loadPositionAnalysis();
            break;
        case 'debug':
            loadDraftBoardDebug();
            // Refresh cache stats when switching to debug tab
            getCacheStats().then(stats => {
                updateCacheStats(stats);
            });
            break;
        case 'chat':
            // Load cached chat messages when switching to chat tab
            loadCachedChatMessages();
            break;
    }
}

// Function to refresh data
function refreshData() {
    updateStatus('Refreshing data...');
    
    // Request fresh data from content script
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {type: 'SCRAPE_NOW'}, function(response) {
                if (response) {
                    console.log('Data refreshed:', response);
                    updateStatus('Data updated');
                    
                    // Reload current tab data
                    const activeTab = document.querySelector('.tab-btn.active');
                    if (activeTab) {
                        loadTabData(activeTab.getAttribute('data-tab'));
                    }
                } else {
                    updateStatus('Error: No response from page');
                }
            });
        } else {
            updateStatus('Error: No active tab found');
        }
    });
}

// Function to clean response text by removing unwanted whitespace
function cleanResponseText(text) {
    if (!text) return text;
    
    return text
        .replace(/^\s+/, '')  // Remove ALL leading whitespace (spaces, tabs, newlines)
        .replace(/\s+$/, '')  // Remove ALL trailing whitespace
        .trim();              // Final trim for any remaining whitespace
}

// Function to convert markdown bold formatting to HTML
function convertMarkdownToHtml(text) {
    if (!text) return text;
    
    // Convert **text** to <strong>text</strong>
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Function to process draft data and get recommendations
function processDraftData(response) {
    if (!response || !response.draftData) {
        console.log('⚠️ No draft data available, showing fallback');
        displayRecommendations(null);
        return;
    }
    
    console.log('✅ Draft data found, processing...');
    
    // Map data to backend models - only process top 10 players for efficiency
    const allAvailablePlayers = Array.isArray(response.draftData.availablePlayers)
        ? response.draftData.availablePlayers.map(mapToPlayerModel)
        : [];
    
    // Limit to top 10 players for processing (reduces API calls and processing time)
    const availablePlayers = allAvailablePlayers.slice(0, 10);
    
    const userTeam = mapToTeamRoster(response.teamData);
    const draftContext = buildDraftContext(response.draftData, response.teamData);
    
    console.log('🗺️ Mapped data for backend:', {
        availablePlayers: availablePlayers,
        userTeam: userTeam,
        draftContext: draftContext
    });
    
    // Log a few sample players to see the structure
    if (availablePlayers.length > 0) {
        console.log('📝 Sample player data:', availablePlayers[0]);
        console.log('📊 Total players found:', allAvailablePlayers.length);
        console.log('🎯 Processing top 10 players:', availablePlayers.length);
    } else {
        console.log('⚠️ No players found in availablePlayers array');
    }
    
    // Check cache first
    const cacheKey = generateCacheKey('recommendation', {
        availablePlayers: availablePlayers,
        userTeam: userTeam,
        draftContext: draftContext
    });
    
    console.log('🔍 Checking cache for key:', cacheKey.substring(0, 50) + '...');
    
    // Temporarily bypass cache to test if that's causing the hang
    console.log('🔄 Bypassing cache for testing...');
    
    // First, enrich player data with API information
    console.log('🔄 Starting player enrichment...');
    console.log('📤 Sending players for enrichment:', availablePlayers);
    
    fetch('http://localhost:8000/api/players/enrich', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            players: availablePlayers,
            source: 'sleeper'
        })
    })
    .then(async res => {
        console.log('📥 Enrich response status:', res.status);
        if (!res.ok) {
            const err = await res.json();
            console.error('❌ Enrich error details:', err);
            throw new Error(JSON.stringify(err));
        }
        return res.json();
    })
    .then(enrichedPlayers => {
        console.log('✅ Enriched players received:', enrichedPlayers);
        
        // Use enriched players if available, otherwise fall back to original
        const playersToUse = enrichedPlayers && enrichedPlayers.length > 0 ? enrichedPlayers : availablePlayers;
        console.log('🎯 Using players for recommendations:', playersToUse.length);
        
        // Now get recommendations with enriched data
        console.log('🔄 Fetching recommendations...');
        return fetch('http://localhost:8000/api/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                available_players: playersToUse,
                user_team: userTeam,
                draft_context: draftContext
            })
        });
    })
    .then(async res => {
        console.log('📥 Backend response status:', res.status);
        if (!res.ok) {
            const err = await res.json();
            console.error('❌ Backend error details:', err);
            throw new Error(JSON.stringify(err));
        }
        return res.json();
    })
    .then(data => {
        console.log('✅ Backend recommendations data:', data);
        // Cache the successful response
        cacheRecommendation(cacheKey, data);
        displayBackendRecommendations(data);
    })
    .catch(err => {
        console.error('❌ Error in recommendation flow:', err);
        
        // Try fallback with original data
        console.log('🔄 Trying fallback with original data...');
        fetch('http://localhost:8000/api/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                available_players: availablePlayers,
                user_team: userTeam,
                draft_context: draftContext
            })
        })
        .then(async res => {
            console.log('📥 Fallback response status:', res.status);
            if (!res.ok) {
                const err = await res.json();
                console.error('❌ Fallback error details:', err);
                throw new Error(JSON.stringify(err));
            }
            return res.json();
        })
        .then(data => {
            console.log('✅ Fallback recommendations data:', data);
            // Cache the fallback response too
            cacheRecommendation(cacheKey, data);
            displayBackendRecommendations(data);
        })
        .catch(fallbackErr => {
            console.error('❌ Fallback also failed:', fallbackErr);
            displayRecommendations(null);
        });
    });
}

// Function to load recommendations
function loadRecommendations() {
    console.log('🔄 Starting loadRecommendations...');
    
    const loadingElement = document.getElementById('recommendation-loading');
    const containerElement = document.getElementById('recommendations-container');
    
    if (loadingElement) {
        console.log('📊 Showing loading element');
        loadingElement.style.display = 'block';
    }
    if (containerElement) {
        console.log('📊 Hiding container element');
        containerElement.style.display = 'none';
    }
    
    console.log('🔍 Querying active tabs...');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        console.log('📋 Found tabs:', tabs);
        
        if (tabs[0]) {
            console.log('📤 Sending GET_DATA message to content script...');
            chrome.tabs.sendMessage(tabs[0].id, {type: 'GET_DATA'}, function(response) {
                console.log('📥 Received response from content script:', response);
                
                if (chrome.runtime.lastError) {
                    console.error('❌ Chrome runtime error:', chrome.runtime.lastError);
                    console.log('🔍 This usually means the content script is not loaded or not responding');
                    
                    // Try to inject the content script manually
                    console.log('🔄 Attempting to inject content script...');
                    chrome.scripting.executeScript({
                        target: { tabId: tabs[0].id },
                        files: ['content.js']
                    }).then(() => {
                        console.log('✅ Content script injected successfully');
                        // Try the request again after a short delay
                        setTimeout(() => {
                            chrome.tabs.sendMessage(tabs[0].id, {type: 'GET_DATA'}, function(retryResponse) {
                                console.log('📥 Retry response from content script:', retryResponse);
                                if (retryResponse && retryResponse.draftData) {
                                    console.log('✅ Successfully got data on retry');
                                    processDraftData(retryResponse);
                                } else {
                                    console.log('❌ Still no data available');
                                    processDraftData(null);
                                }
                            });
                        }, 1000);
                    }).catch(err => {
                        console.error('❌ Failed to inject content script:', err);
                        processDraftData(null);
                    });
                    return;
                }
                
                if (response && response.draftData) {
                    console.log('✅ Draft data found, processing...');
                    processDraftData(response);
                } else {
                    console.log('⚠️ No draft data available');
                    processDraftData(null);
                }
            });
        } else {
            console.log('❌ No active tab found');
            displayRecommendations(null);
        }
    });
}

// Function to display backend recommendations
function displayBackendRecommendations(data) {
    console.log('🎨 Displaying backend recommendations:', data);
    
    const loadingElement = document.getElementById('recommendation-loading');
    const containerElement = document.getElementById('recommendations-container');
    
    if (loadingElement) {
        console.log('📊 Hiding loading element');
        loadingElement.style.display = 'none';
    }
    if (containerElement) {
        console.log('📊 Showing container element');
        containerElement.style.display = 'block';
    }
    
    if (!data || !data.primary_recommendation || !data.primary_recommendation.player) {
        console.log('❌ No valid recommendation data found');
        document.getElementById('main-player-name').textContent = 'No players available';
        document.getElementById('main-player-position').textContent = '';
        document.getElementById('main-player-team').textContent = '';
        document.getElementById('main-pick-reasoning').textContent = 'No draft data available. Make sure you are on a Sleeper draft page.';
        return;
    }
    
    console.log('✅ Valid recommendation data found, displaying...');
    
    // Display main recommendation
    const main = data.primary_recommendation.player;
    console.log('🏆 Main recommendation player:', main);
    
    document.getElementById('main-player-name').textContent = main.name || 'Unknown Player';
    document.getElementById('main-player-position').textContent = main.position || 'Unknown Position';
    document.getElementById('main-player-team').textContent = main.team || 'Unknown Team';
    // Format points with fallbacks
    const formatPoints = (points) => {
        if (points === null || points === undefined) return 'N/A';
        return typeof points === 'number' ? points.toFixed(1) : points.toString();
    };
    
    document.getElementById('main-projected-points').textContent = formatPoints(main.projected_points);
    document.getElementById('main-value-score').textContent = formatPoints(main.value_score);
    document.getElementById('main-pick-reasoning').textContent = data.primary_recommendation.reasoning || 'No reasoning available';
    
    // Store the recommendations data globally for switching
    window.currentRecommendations = {
        data: data,
        primaryIndex: 0
    };
    
    // Display alternative recommendations
    for (let i = 1; i <= 2; i++) {
        const alt = data.alternative_recommendations && data.alternative_recommendations[i-1];
        console.log(`🔀 Alternative ${i}:`, alt);
        
        if (alt && alt.player) {
            document.getElementById(`alt${i}-player-name`).textContent = alt.player.name || 'Unknown Player';
            document.getElementById(`alt${i}-player-position`).textContent = alt.player.position || 'Unknown Position';
            document.getElementById(`alt${i}-player-team`).textContent = alt.player.team || 'Unknown Team';
            document.getElementById(`alt${i}-value-score`).textContent = alt.player.value_score || 'N/A';
            document.getElementById(`alt${i}-pick-reasoning`).textContent = alt.reasoning || 'No reasoning available';
        } else {
            document.getElementById(`alt${i}-player-name`).textContent = 'No alternative available';
            document.getElementById(`alt${i}-player-position`).textContent = '';
            document.getElementById(`alt${i}-player-team`).textContent = '';
            document.getElementById(`alt${i}-value-score`).textContent = '';
            document.getElementById(`alt${i}-pick-reasoning`).textContent = '';
        }
    }
    
    console.log('✅ Adding click event listeners...');
    // Add click event listeners for interactive selection
    addRecommendationClickListeners();
    console.log('✅ Display complete!');
}

// Function to display recommendations
function displayRecommendations(draftData) {
    const loadingElement = document.getElementById('recommendation-loading');
    const containerElement = document.getElementById('recommendations-container');
    
    if (loadingElement) loadingElement.style.display = 'none';
    if (containerElement) containerElement.style.display = 'block';
    
    if (!draftData || !draftData.availablePlayers || draftData.availablePlayers.length === 0) {
        document.getElementById('main-player-name').textContent = 'No players available';
        document.getElementById('main-player-position').textContent = '';
        document.getElementById('main-player-team').textContent = '';
        document.getElementById('main-pick-reasoning').textContent = 'No draft data available. Make sure you are on a Sleeper draft page.';
        return;
    }
    
    // Get top 3 available players
    const topPlayers = draftData.availablePlayers.slice(0, 3);
    
    // Store the recommendations data globally for switching
    window.currentRecommendations = {
        players: topPlayers,
        draftData: draftData
    };
    
    // Display the main recommendation (first player)
    displayMainRecommendation(topPlayers[0], draftData);
    
    // Display alternative recommendations
    if (topPlayers.length > 1) {
        displayAlternativeRecommendation(1, topPlayers[1], draftData);
    }
    if (topPlayers.length > 2) {
        displayAlternativeRecommendation(2, topPlayers[2], draftData);
    }
    
    // Add click event listeners
    addRecommendationClickListeners();
}

// Function to display main recommendation
function displayMainRecommendation(player, draftData) {
    document.getElementById('main-player-name').textContent = player.name || 'Unknown Player';
    document.getElementById('main-player-position').textContent = player.position || 'Unknown Position';
    document.getElementById('main-player-team').textContent = player.team || 'Unknown Team';
    
    // Generate reasoning
    let reasoning = `This player is currently available and ranked at the top of the available players list. `;
    if (draftData.currentPick) {
        reasoning += `You are currently at ${draftData.currentPick}. `;
    }
    if (draftData.draftRound) {
        reasoning += `This is round ${draftData.draftRound}. `;
    }
    reasoning += `Consider your team's needs and positional scarcity when making your final decision.`;
    
    document.getElementById('main-pick-reasoning').textContent = reasoning;
    
    // Mock stats (you can replace with real data later)
    document.getElementById('main-projected-points').textContent = '165';
    document.getElementById('main-value-score').textContent = '8.5';
}

// Function to display alternative recommendation
function displayAlternativeRecommendation(index, player, draftData) {
    const nameElement = document.getElementById(`alt${index}-player-name`);
    const positionElement = document.getElementById(`alt${index}-player-position`);
    const teamElement = document.getElementById(`alt${index}-player-team`);
    const valueElement = document.getElementById(`alt${index}-value-score`);
    const reasoningElement = document.getElementById(`alt${index}-pick-reasoning`);
    
    if (nameElement) nameElement.textContent = player.name || 'Unknown Player';
    if (positionElement) positionElement.textContent = player.position || 'Unknown Position';
    if (teamElement) teamElement.textContent = player.team || 'Unknown Team';
    if (valueElement) valueElement.textContent = (8.5 - index * 0.5).toFixed(1);
    
    // Generate reasoning for alternative
    let reasoning = `Solid alternative pick. `;
    if (draftData.currentPick) {
        reasoning += `Available at ${draftData.currentPick}. `;
    }
    reasoning += `Good value for this position.`;
    
    if (reasoningElement) reasoningElement.textContent = reasoning;
}

// Function to add click event listeners
function addRecommendationClickListeners() {
    // Add click listener to main recommendation
    const mainRecommendation = document.getElementById('main-recommendation');
    if (mainRecommendation) {
        // Remove existing listeners to prevent duplicates
        mainRecommendation.removeEventListener('click', mainRecommendation.clickHandler);
        mainRecommendation.clickHandler = function() {
            selectRecommendation(0);
        };
        mainRecommendation.addEventListener('click', mainRecommendation.clickHandler);
    }
    
    // Add click listeners to alternative recommendations
    const altRecommendations = document.querySelectorAll('.alt-recommendation');
    altRecommendations.forEach((altRec, index) => {
        // Remove existing listeners to prevent duplicates
        altRec.removeEventListener('click', altRec.clickHandler);
        altRec.clickHandler = function() {
            selectRecommendation(index + 1);
        };
        altRec.addEventListener('click', altRec.clickHandler);
    });
}

// Function to select a recommendation
function selectRecommendation(index) {
    if (!window.currentRecommendations || !window.currentRecommendations.data) {
        return;
    }
    
    const data = window.currentRecommendations.data;
    
    // If clicking on main recommendation (index 0), do nothing (it's already selected)
    if (index === 0) {
        return;
    }
    
    // If clicking on an alternative, swap it with the main recommendation
    const alternativeIndex = index - 1;
    if (data.alternative_recommendations && data.alternative_recommendations[alternativeIndex]) {
        const alternative = data.alternative_recommendations[alternativeIndex];
        
        // Create new data structure with the alternative as primary
        const newData = {
            primary_recommendation: {
                player: alternative.player,
                reasoning: alternative.reasoning,
                confidence_score: alternative.confidence_score
            },
            alternative_recommendations: [
                {
                    player: data.primary_recommendation.player,
                    reasoning: data.primary_recommendation.reasoning,
                    confidence_score: data.primary_recommendation.confidence_score
                },
                ...data.alternative_recommendations.filter((_, i) => i !== alternativeIndex)
            ],
            strategy_notes: data.strategy_notes,
            next_picks_suggestion: data.next_picks_suggestion
        };
        
        // Update the stored recommendations
        window.currentRecommendations.data = newData;
        window.currentRecommendations.primaryIndex = index;
        
        // Update the display
        displayBackendRecommendations(newData);
        
        // Update visual states
        updateRecommendationVisualStates(index);
    }
}

// Function to update visual states
function updateRecommendationVisualStates(selectedIndex) {
    const mainRecommendation = document.getElementById('main-recommendation');
    const altRecommendations = document.querySelectorAll('.alt-recommendation');
    
    // Reset all states
    mainRecommendation.classList.remove('demoted');
    altRecommendations.forEach(alt => alt.classList.remove('selected'));
    
    // Apply new states
    if (selectedIndex === 0) {
        // Main recommendation is selected
        mainRecommendation.classList.remove('demoted');
    } else {
        // Alternative recommendation is selected
        mainRecommendation.classList.add('demoted');
        if (altRecommendations[selectedIndex - 1]) {
            altRecommendations[selectedIndex - 1].classList.add('selected');
        }
    }
}

// Function to load position analysis
function loadPositionAnalysis() {
    const loadingElement = document.getElementById('position-loading');
    const analysisElement = document.getElementById('position-analysis');
    
    if (loadingElement) loadingElement.style.display = 'block';
    if (analysisElement) analysisElement.style.display = 'none';
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {type: 'GET_DATA'}, function(response) {
                if (response && response.teamData) {
                    displayPositionAnalysis(response.teamData);
                } else {
                    displayPositionAnalysis(null);
                }
            });
        } else {
            displayPositionAnalysis(null);
        }
    });
}

// Function to display position analysis
function displayPositionAnalysis(teamData) {
    const loadingElement = document.getElementById('position-loading');
    const analysisElement = document.getElementById('position-analysis');
    
    if (loadingElement) loadingElement.style.display = 'none';
    if (analysisElement) analysisElement.style.display = 'block';
    
    const positionCountsElement = document.getElementById('position-counts');
    const priorityListElement = document.getElementById('priority-list');
    
    if (!teamData || !teamData.positionCounts) {
        positionCountsElement.innerHTML = '<p>No team data available</p>';
        priorityListElement.innerHTML = '<p>No team data available</p>';
    return;
  }
    
    // Display position counts
    let countsHTML = '';
    const positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'];
    positions.forEach(pos => {
        const count = teamData.positionCounts[pos] || 0;
        countsHTML += `<div class="position-count">
            <span class="position">${pos}</span>
            <span class="count">${count}</span>
        </div>`;
    });
    positionCountsElement.innerHTML = countsHTML;
    
    // Generate priority recommendations
    let priorityHTML = '';
    const recommendations = generatePositionRecommendations(teamData.positionCounts);
    recommendations.forEach(rec => {
        priorityHTML += `<div class="priority-item ${rec.priority}">
            <span class="position">${rec.position}</span>
            <span class="reason">${rec.reason}</span>
        </div>`;
    });
    priorityListElement.innerHTML = priorityHTML;
}

// Function to generate position recommendations
function generatePositionRecommendations(positionCounts) {
    const recommendations = [];
    
    // Simple logic - you can enhance this
    if (!positionCounts['RB'] || positionCounts['RB'] < 2) {
        recommendations.push({
            position: 'RB',
            priority: 'high',
            reason: 'Need more running backs'
        });
    }
    
    if (!positionCounts['WR'] || positionCounts['WR'] < 2) {
        recommendations.push({
            position: 'WR',
            priority: 'high',
            reason: 'Need more wide receivers'
        });
    }
    
    if (!positionCounts['QB']) {
        recommendations.push({
            position: 'QB',
            priority: 'medium',
            reason: 'Need a quarterback'
        });
    }
    
    if (!positionCounts['TE']) {
        recommendations.push({
            position: 'TE',
            priority: 'medium',
            reason: 'Need a tight end'
        });
    }
    
    return recommendations;
}

// Function to load draft board debug data
function loadDraftBoardDebug() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {type: 'GET_DRAFT_BOARD_TEAMS'}, function(response) {
                displayDraftBoardDebug(response);
            });
        } else {
            displayDraftBoardDebug(null);
        }
    });
}

// Function to display draft board debug data
function displayDraftBoardDebug(response) {
    const debugElement = document.getElementById('draft-board-debug');
    
    if (!response || !response.draftBoardTeams) {
        debugElement.innerHTML = '<p>No draft board data available</p>';
        return;
    }
    
    let debugHTML = '<div class="debug-teams">';
    response.draftBoardTeams.forEach((team, teamIndex) => {
        debugHTML += `<div class="debug-team">
            <h4>${team.teamName}</h4>
            <div class="debug-picks">`;
        
        team.picks.forEach((pick, pickIndex) => {
            if (pick) {
                debugHTML += `<div class="debug-pick">
                    <span class="pick-number">${pickIndex + 1}</span>
                    <span class="player-name">${pick.playerName}</span>
                    <span class="position">${pick.position}</span>
                    <span class="nfl-team">${pick.nflTeam}</span>
                </div>`;
            } else {
                debugHTML += `<div class="debug-pick empty">
                    <span class="pick-number">${pickIndex + 1}</span>
                    <span class="player-name">Not drafted</span>
                </div>`;
            }
        });
        
        debugHTML += `</div></div>`;
    });
    debugHTML += '</div>';
    
    debugElement.innerHTML = debugHTML;
}

// Function to send chat message
function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    if (!chatInput || !chatInput.value.trim()) return;
    const message = chatInput.value.trim();
    // Add user message to chat
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user-message';
    userMessageDiv.innerHTML = `
        <div class="message-content">
            <p>${message}</p>
        </div>
    `;
    chatMessages.appendChild(userMessageDiv);
    // Clear input
    chatInput.value = '';
    
    // Try to get draft context, but make API call regardless
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {type: 'GET_DATA'}, function(response) {
                let draftContext = null;
                let userTeam = null;
                
                if (response && response.draftData) {
                    draftContext = buildDraftContext(response.draftData, response.teamData);
                    userTeam = mapToTeamRoster(response.teamData);
                }
                
                // Check cache first
                const cacheData = {
                    message: message,
                    draftContext: draftContext || null,
                    userTeam: userTeam || null
                };
                
                const cacheKey = generateCacheKey('chat', cacheData);
                
                console.log('🔍 Checking chat cache for key:', cacheKey.substring(0, 50) + '...');
                console.log('📊 Cache data:', {
                    message: message,
                    draftContext: draftContext ? 'present' : 'null',
                    userTeam: userTeam ? 'present' : 'null'
                });
                
                // Temporarily bypass cache for testing
                console.log('🔄 Bypassing chat cache for testing...');
                
                // Always make the API call, even without draft data
                fetch('http://localhost:8000/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        draft_context: draftContext,
                        user_team: userTeam
                    })
                })
                .then(async res => {
                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(JSON.stringify(err));
                    }
                    return res.json();
                })
                .then(data => {
                    // Cache the successful response with both user message and AI response
                    const cacheData = {
                        userMessage: message,
                        aiResponse: data
                    };
                    console.log('💾 Attempting to cache chat response for key:', cacheKey.substring(0, 50) + '...');
                    console.log('📊 Data to cache:', cacheData);
                    cacheChat(cacheKey, cacheData);
                    
                    const aiMessageDiv = document.createElement('div');
                    aiMessageDiv.className = 'message ai-message';
                    aiMessageDiv.innerHTML = `<div class="message-content">${convertMarkdownToHtml(cleanResponseText(data.response || 'No response from AI.'))}</div>`;
                    chatMessages.appendChild(aiMessageDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                })
                .catch(err => {
                    console.error('Chat API error:', err);
                    const aiMessageDiv = document.createElement('div');
                    aiMessageDiv.className = 'message ai-message';
                    aiMessageDiv.innerHTML = `<div class="message-content">Error contacting AI backend.\n${convertMarkdownToHtml(cleanResponseText(err))}</div>`;
                    chatMessages.appendChild(aiMessageDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                });
            });
        } else {
            // No active tab, still try to make the API call
            const cacheData = {
                message: message,
                draftContext: null,
                userTeam: null
            };
            
            const cacheKey = generateCacheKey('chat', cacheData);
            
            console.log('🔍 Checking chat cache for key (no tab):', cacheKey.substring(0, 50) + '...');
            console.log('📊 Cache data (no tab):', {
                message: message,
                draftContext: 'null',
                userTeam: 'null'
            });
            
            // Temporarily bypass cache for testing
            console.log('🔄 Bypassing chat cache for testing (no tab)...');
            
            fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    draft_context: null,
                    user_team: null
                })
            })
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(JSON.stringify(err));
                }
                return res.json();
            })
            .then(data => {
                // Cache the successful response
                const cacheData = {
                    userMessage: message,
                    aiResponse: data
                };
                cacheChat(cacheKey, cacheData);
                
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.innerHTML = `<div class="message-content">${convertMarkdownToHtml(cleanResponseText(data.response || 'No response from AI.'))}</div>`;
                chatMessages.appendChild(aiMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(err => {
                console.error('Chat API error:', err);
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.innerHTML = `<div class="message-content">Error contacting AI backend.\n${convertMarkdownToHtml(cleanResponseText(err))}</div>`;
                chatMessages.appendChild(aiMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        }
    });
}

// Function to update status
function updateStatus(message) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// Function to sync player data from APIs
function syncPlayerData() {
    const syncButton = document.getElementById('sync-data');
    if (syncButton) {
        syncButton.classList.add('loading');
        syncButton.textContent = '🔄 Syncing...';
        syncButton.disabled = true;
    }
    
    console.log('Syncing player data from APIs...');
    
    // Sync from Sleeper API
    fetch('http://localhost:8000/api/players/sync/sleeper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(async res => {
        if (!res.ok) {
            const err = await res.json();
            throw new Error(JSON.stringify(err));
        }
        return res.json();
    })
    .then(sleeperPlayers => {
        console.log(`Synced ${sleeperPlayers.length} players from Sleeper`);
        
        // Also sync from ESPN API
        return fetch('http://localhost:8000/api/players/sync/espn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    })
    .then(async res => {
        if (!res.ok) {
            const err = await res.json();
            throw new Error(JSON.stringify(err));
        }
        return res.json();
    })
    .then(espnPlayers => {
        console.log(`Synced ${espnPlayers.length} players from ESPN`);
        
        // Update button state
        if (syncButton) {
            syncButton.classList.remove('loading');
            syncButton.textContent = '✅ Synced';
            syncButton.disabled = false;
            
            // Reset button text after 3 seconds
            setTimeout(() => {
                syncButton.textContent = '🔄 Sync Data';
            }, 3000);
        }
        
        // Refresh current recommendations with new data
        loadRecommendations();
    })
    .catch(err => {
        console.error('Error syncing player data:', err);
        
        // Reset button state on error
        if (syncButton) {
            syncButton.classList.remove('loading');
            syncButton.textContent = '❌ Error';
            syncButton.disabled = false;
            
            // Reset button text after 3 seconds
            setTimeout(() => {
                syncButton.textContent = '🔄 Sync Data';
            }, 3000);
        }
    });
}

// Function to clear chat messages
function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        // Keep only the initial welcome message
        chatMessages.innerHTML = `
            <div class="message ai-message">
                <div class="message-content">
Hello! I'm your fantasy football draft assistant. Ask me anything about players, strategies, or your team composition!
                </div>
            </div>
        `;
        console.log('🗑️ Chat cleared from UI');
        
        // Also clear the chat cache in the backend
        fetch('http://localhost:8000/api/chat/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(async res => {
            if (!res.ok) {
                const err = await res.json();
                throw new Error(JSON.stringify(err));
            }
            return res.json();
        })
        .then(data => {
            console.log('✅ Chat cache cleared from backend:', data);
        })
        .catch(err => {
            console.error('❌ Error clearing chat cache:', err);
        });
    }
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add clear chat button event listener
    const clearChatBtn = document.getElementById('clear-chat');
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', clearChat);
    }
});

// Initialize popup
console.log('Fantasy Football Draft Helper: Popup script initialized');

// Clear expired chat messages on startup
clearExpiredChatMessages();

// Load initial data
loadTabData('recommendations');