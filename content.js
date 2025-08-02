// Content script for Sleeper.com
// This script runs on Sleeper pages to extract draft and team data

(function() {
// Prevent double-initialization
if (window.hasRunDraftHelperContentScript) {
    // Already initialized, don't run again
    return;
}
window.hasRunDraftHelperContentScript = true;

// Store scraped data as a property of window to avoid redeclaration
window.scrapedData = window.scrapedData || {
    draftData: null,
    teamData: null,
    lastUpdate: null
};

console.log('Fantasy Football Draft Helper: Content script loaded');

// Check if extension context is valid
function isExtensionContextValid() {
    try {
        return typeof chrome !== 'undefined' && 
               chrome.runtime && 
               chrome.runtime.sendMessage;
    } catch (error) {
        return false;
    }
}

// Function to safely send messages to the extension
function safeSendMessage(message) {
    if (!isExtensionContextValid()) {
        console.log('Extension context not available - skipping message send');
        return;
    }
    
    try {
        chrome.runtime.sendMessage(message).catch(error => {
            console.log('Message send error (normal during reload):', error.message);
        });
    } catch (error) {
        console.log('Extension context error (normal during reload):', error.message);
    }
}

// Function to safely add message listener
function safeAddMessageListener() {
    if (!isExtensionContextValid()) {
        console.log('Extension context not available - skipping message listener');
        return;
    }
    
    try {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            console.log('📥 Content script received message:', message.type);
            
            if (message.type === 'GET_DATA') {
                console.log('📤 Sending scraped data:', window.scrapedData);
                sendResponse(window.scrapedData);
            } else if (message.type === 'SCRAPE_NOW') {
                console.log('🔄 Scraping data now...');
                const data = scrapeAllData();
                console.log('📤 Sending fresh scraped data:', data);
                sendResponse(data);
            } else if (message.type === "GET_DRAFT_BOARD_TEAMS") {
                console.log('📤 Sending draft board teams:', window.draftBoardTeamsDebug);
                sendResponse({ draftBoardTeams: window.draftBoardTeamsDebug });
            }
            
            // Return true to indicate we will send a response asynchronously
            return true;
        });
    } catch (error) {
        console.log('Error adding message listener:', error.message);
    }
}

// Function to scrape draft data from Sleeper
function scrapeDraftData() {
    console.log('🔍 Starting draft data scraping...');
    
    try {
        const draftData = {
            availablePlayers: [],
            currentPick: null,
            draftPosition: null,
            draftRound: null
        };

        // Look for available players in the draft board
        // Based on Sleeper's actual HTML structure
        const playerElements = document.querySelectorAll('.player-rank-item2');
        console.log('📊 Found player elements:', playerElements.length);

        // Extract player information
        playerElements.forEach((element, index) => {
            console.log(`🔍 Processing player element ${index + 1}:`, element);
            const player = extractPlayerInfo(element);
            if (player && player.name) {
                console.log('✅ Extracted player:', player);
                draftData.availablePlayers.push(player);
            } else {
                console.log('❌ Failed to extract player from element:', element);
            }
        });

        console.log('📊 Total players extracted:', draftData.availablePlayers.length);

        // Get current pick information from the cell with current-pick class
        const currentPickElement = document.querySelector('.cell.current-pick');
        if (currentPickElement) {
            const cellId = currentPickElement.id;
            const pickNumber = cellId ? cellId.replace('draft-cell-', '') : 'Unknown';
            draftData.currentPick = `Pick ${pickNumber}`;
        }

        // Calculate draft round based on current pick number
        if (draftData.currentPick && draftData.currentPick !== 'Pick Unknown') {
            const pickNumber = parseInt(draftData.currentPick.replace('Pick ', ''));
            if (!isNaN(pickNumber)) {
                // Assuming 12 teams, calculate round
                draftData.draftRound = Math.ceil(pickNumber / 12);
            }
        }

        return draftData;
    } catch (error) {
        console.error('Error scraping draft data:', error);
        return null;
    }
}

// Function to extract player information from a player element
function extractPlayerInfo(element) {
    console.log('🔍 Extracting player info from element:', element);
    
    try {
        const player = {
            name: '',
            position: '',
            team: '',
            available: true,
            stats: {},
            projected_points: null
        };

        // Get player name from the name-wrapper
        const nameElement = element.querySelector('.name-wrapper');
        console.log('📝 Name element found:', nameElement);
        
        if (nameElement && nameElement.textContent.trim()) {
            let rawName = nameElement.textContent.trim();
            console.log('📝 Raw name text:', rawName);
            
            // Clean up the name - remove any position or team info that might be concatenated
            const positions = ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'];
            let cleanName = rawName;
            
            // Find and remove position from the name
            for (const pos of positions) {
                const posIndex = cleanName.indexOf(pos);
                if (posIndex !== -1) {
                    cleanName = cleanName.substring(0, posIndex).trim();
                    console.log('🧹 Removed position from name:', pos);
                    break;
                }
            }
            
            // Remove team abbreviations that might be at the end
            const teamPattern = /\s+[A-Z]{2,3}$/;
            cleanName = cleanName.replace(teamPattern, '').trim();
            console.log('🧹 Cleaned name:', cleanName);
            
            player.name = cleanName || rawName; // Fallback to original if cleaning fails
        } else {
            console.log('❌ No name element found');
        }

        // Get position from the element's classes (RB, QB, WR, TE, etc.)
        const elementClasses = element.className.split(' ');
        console.log('🏷️ Element classes:', elementClasses);
        
        const positionClass = elementClasses.find(cls => ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'].includes(cls));
        if (positionClass) {
            player.position = positionClass;
            console.log('🏷️ Found position from classes:', positionClass);
        }

        // Get team from the position div which contains team info
        const positionDiv = element.querySelector('.position');
        console.log('🏈 Position div found:', positionDiv);
        
        if (positionDiv) {
            const teamSpan = positionDiv.querySelector('.team');
            if (teamSpan && teamSpan.textContent.trim()) {
                let teamText = teamSpan.textContent.trim();
                console.log('🏈 Raw team text:', teamText);
                
                // Clean up team name - remove any position info
                const positions = ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'];
                for (const pos of positions) {
                    teamText = teamText.replace(pos, '').trim();
                }
                
                player.team = teamText || 'Unknown';
                console.log('🏈 Cleaned team:', player.team);
            } else {
                player.team = 'Unknown'; // Default if team info not found
                console.log('🏈 No team span found, using default');
            }
        } else {
            player.team = 'Unknown'; // Default if team info not found
            console.log('🏈 No position div found, using default');
        }

        // Extract projected points from the HTML structure
        // Based on the actual HTML structure: <div class="proj-pts col-sml stat-cell"><span class="value">150.2</span></div>
        const projectedPointsSelectors = [
            '.proj-pts.col-sml.stat-cell .value',
            '.proj-pts .value',
            '.proj-pts.col-sml.stat-cell',
            '.proj-pts',
            '[class*="proj-pts"] .value',
            '[class*="proj"] .value'
        ];
        
        console.log('📊 Looking for projected points...');
        let projectedPoints = null;
        
        for (const selector of projectedPointsSelectors) {
            const projectedElement = element.querySelector(selector);
            if (projectedElement) {
                const projectedText = projectedElement.textContent.trim();
                console.log('📊 Found projected points element with selector:', selector);
                console.log('📊 Projected points text:', projectedText);
                
                // Try to parse the projected points as a number
                const projectedValue = parseFloat(projectedText);
                if (!isNaN(projectedValue)) {
                    projectedPoints = projectedValue;
                    console.log('✅ Parsed projected points:', projectedValue);
                    break;
                } else {
                    console.log('❌ Could not parse projected points as number:', projectedText);
                }
            }
        }
        
        if (projectedPoints !== null) {
            player.projected_points = projectedPoints;
            console.log('✅ Set projected points:', projectedPoints);
        } else {
            console.log('❌ No projected points found with any selector');
        }

        // Extract additional stats from the HTML structure
        // Rank: <div class="rank">58</div>
        const rankElement = element.querySelector('.rank');
        if (rankElement) {
            const rankText = rankElement.textContent.trim();
            const rankValue = parseInt(rankText);
            if (!isNaN(rankValue)) {
                player.rank = rankValue;
                console.log('✅ Parsed rank:', rankValue);
            }
        }

        // ADP: <div class="adp col-sml stat-cell"><span class="value">58.7</span></div>
        const adpElement = element.querySelector('.adp.col-sml.stat-cell .value');
        if (adpElement) {
            const adpText = adpElement.textContent.trim();
            const adpValue = parseFloat(adpText);
            if (!isNaN(adpValue)) {
                player.adp = adpValue;
                console.log('✅ Parsed ADP:', adpValue);
            }
        }

        // Bye week: <div class="bye col-sml stat-cell col-border-right"><span class="value">12</span></div>
        const byeElement = element.querySelector('.bye.col-sml.stat-cell .value');
        if (byeElement) {
            const byeText = byeElement.textContent.trim();
            const byeValue = parseInt(byeText);
            if (!isNaN(byeValue)) {
                player.bye_week = byeValue;
                console.log('✅ Parsed bye week:', byeValue);
            }
        }

        // Extract other stats if available
        const statElements = element.querySelectorAll('.stat, [data-testid*="stat"]');
        console.log('📊 Stat elements found:', statElements.length);
        
        statElements.forEach(statElement => {
            const label = statElement.querySelector('.label, .stat-label');
            const value = statElement.querySelector('.value, .stat-value');
            if (label && value) {
                const labelText = label.textContent.trim().toLowerCase();
                const valueText = value.textContent.trim();
                player.stats[labelText] = valueText;
                console.log('📊 Stat:', labelText, '=', valueText);
            }
        });

        console.log('✅ Final extracted player:', player);
        return player;
    } catch (error) {
        console.error('❌ Error extracting player info:', error);
        return null;
    }
}

// Function to scrape team data
function scrapeTeamData() {
    try {
        const teamData = {
            players: [],
            positionCounts: {},
            teamName: '',
            leagueInfo: {}
        };

        // Find the user's team column in the draft board
        const draftBoard = document.querySelector('.draft-board');
        if (!draftBoard) {
            console.log('No draft board found');
            return teamData;
        }

        // Look for the user's team column - it might be highlighted or have a special class
        let userTeamColumn = null;
        const teamColumns = draftBoard.querySelectorAll('.team-column');
        
        // Try to find the user's team by looking for highlighted/active columns
        teamColumns.forEach((col, index) => {
            // Check if this column is highlighted as the current user's team
            const isUserTeam = col.classList.contains('user-team') || 
                              col.classList.contains('my-team') ||
                              col.classList.contains('active') ||
                              col.classList.contains('current-user');
            
            if (isUserTeam) {
                userTeamColumn = col;
                console.log(`Found user team column at index ${index}`);
            }
        });

        // If we can't find a specific user team column, try to identify it by looking for the current pick
        if (!userTeamColumn) {
            const currentPickCell = document.querySelector('.cell.current-pick');
            if (currentPickCell) {
                // Find which column contains the current pick
                const currentPickContainer = currentPickCell.closest('.team-column');
                if (currentPickContainer) {
                    userTeamColumn = currentPickContainer;
                    console.log('Found user team column via current pick');
                }
            }
        }

        // If still no user team found, use the first column as fallback
        if (!userTeamColumn && teamColumns.length > 0) {
            userTeamColumn = teamColumns[0];
            console.log('Using first team column as fallback');
        }

        if (!userTeamColumn) {
            console.log('No user team column found');
            return teamData;
        }

        // Get team name from the header
        const header = userTeamColumn.querySelector('.header, .header-text');
        if (header && header.textContent.trim()) {
            teamData.teamName = header.textContent.trim();
        } else {
            teamData.teamName = 'My Team';
        }

        // Get all drafted players from the user's team column only
        const userTeamCells = userTeamColumn.querySelectorAll('.cell.drafted');
        const userTeamPlayers = [];

        userTeamCells.forEach(cell => {
            const playerElement = cell.querySelector('.player');
            if (playerElement) {
                const playerNameElement = playerElement.querySelector('.player-name');
                const positionElement = playerElement.querySelector('.position');
                
                if (playerNameElement) {
                    const player = {
                        name: playerNameElement.textContent.trim(),
                        position: '',
                        team: '',
                        teamName: teamData.teamName
                    };
                    
                    if (positionElement) {
                        const positionText = positionElement.textContent.trim();
                        const parts = positionText.split('-').map(part => part.trim());
                        if (parts.length >= 2) {
                            player.position = parts[0];
                            player.team = parts[parts.length - 1];
                        }
                    }
                    
                    // Also check for position in cell classes
                    const cellClasses = cell.className.split(' ');
                    const positionClass = cellClasses.find(cls => ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'].includes(cls));
                    if (positionClass && !player.position) {
                        player.position = positionClass;
                    }
                    
                    if (player.name && player.position) {
                        userTeamPlayers.push(player);
                        teamData.players.push(player);
                        
                        // Count positions for user's team only
                        teamData.positionCounts[player.position] = 
                            (teamData.positionCounts[player.position] || 0) + 1;
                    }
                }
            }
        });

        // For debugging, also collect all drafted players across all teams
        const allDraftedPlayers = [];
        const allDraftedCells = document.querySelectorAll('.cell.drafted');
        allDraftedCells.forEach(cell => {
            const playerElement = cell.querySelector('.player');
            if (playerElement) {
                const playerNameElement = playerElement.querySelector('.player-name');
                const positionElement = playerElement.querySelector('.position');
                let teamName = 'Unknown Team';
                
                // Try to get team name from parent column
                const parentColumn = cell.closest('.team-column');
                if (parentColumn) {
                    const parentHeader = parentColumn.querySelector('.header, .header-text');
                    if (parentHeader) {
                        teamName = parentHeader.textContent.trim();
                    }
                }
                
                if (playerNameElement) {
                    const player = {
                        name: playerNameElement.textContent.trim(),
                        position: '',
                        team: '',
                        teamName: teamName
                    };
                    
                    if (positionElement) {
                        const positionText = positionElement.textContent.trim();
                        const parts = positionText.split('-').map(part => part.trim());
                        if (parts.length >= 2) {
                            player.position = parts[0];
                            player.team = parts[parts.length - 1];
                        }
                    }
                    
                    const cellClasses = cell.className.split(' ');
                    const positionClass = cellClasses.find(cls => ['RB', 'QB', 'WR', 'TE', 'K', 'DEF'].includes(cls));
                    if (positionClass && !player.position) {
                        player.position = positionClass;
                    }
                    
                    if (player.name && player.position) {
                        allDraftedPlayers.push(player);
                    }
                }
            }
        });

        // Expose debug data
        window.draftedPlayersDebug = allDraftedPlayers;
        window.userTeamPlayersDebug = userTeamPlayers;
        
        console.log(`User team (${teamData.teamName}) players:`, userTeamPlayers);
        console.log(`User team position counts:`, teamData.positionCounts);
        
        return teamData;
    } catch (error) {
        console.error('Error scraping team data:', error);
        return null;
    }
}

function scrapeDraftBoardTeams() {
    try {
        const board = document.querySelector('.draft-board');
        if (!board) return null;
        const teamColumns = board.querySelectorAll('.team-column');
        const teams = [];
        teamColumns.forEach((col, colIdx) => {
            // Try to get team name from .header or .header-text
            let teamName = 'Team ' + (colIdx + 1);
            const header = col.querySelector('.header, .header-text');
            if (header && header.textContent.trim()) {
                teamName = header.textContent.trim();
            }
            const picks = [];
            const cellContainers = col.querySelectorAll('.cell-container');
            cellContainers.forEach((cellContainer, roundIdx) => {
                const draftedCell = cellContainer.querySelector('.cell.drafted');
                if (draftedCell) {
                    const playerNameEl = draftedCell.querySelector('.player-name');
                    const positionEl = draftedCell.querySelector('.position');
                    let playerName = playerNameEl ? playerNameEl.textContent.trim() : '';
                    let position = '';
                    let nflTeam = '';
                    if (positionEl) {
                        // The .position element contains lines like "QB", "-", "BUF"
                        const lines = positionEl.textContent.split('\n').map(l => l.trim()).filter(Boolean);
                        if (lines.length >= 2) {
                            position = lines[0];
                            nflTeam = lines[lines.length - 1];
                        }
                    }
                    picks.push({
      playerName,
                        position,
                        nflTeam,
                        pickNumber: draftedCell.id ? draftedCell.id.replace('draft-cell-', '') : ''
                    });
                } else {
                    picks.push(null); // No player drafted in this round for this team
                }
            });
            teams.push({
                teamName,
                picks
            });
        });
        window.draftBoardTeamsDebug = teams;
        return teams;
    } catch (error) {
        console.error('Error scraping draft board teams:', error);
        return null;
    }
}

// Function to scrape all data
function scrapeAllData() {
    try {
        const draftData = scrapeDraftData();
        const teamData = scrapeTeamData();
        const draftBoardTeams = scrapeDraftBoardTeams();
        console.log("SCRAPED draftData:", draftData);
        console.log("SCRAPED teamData:", teamData);
        console.log("SCRAPED draftBoardTeams:", draftBoardTeams);
        window.scrapedData = {
            draftData,
            teamData,
            draftBoardTeams,
            lastUpdate: Date.now()
        };
        
        // Use safe message sending
        safeSendMessage({
            type: 'DATA_UPDATED',
            data: window.scrapedData
        });
        
        return window.scrapedData;
    } catch (error) {
        console.error('Error in scrapeAllData:', error);
        return window.scrapedData; // Return existing data if scraping fails
    }
}

// Auto-scrape data periodically
function startAutoScrape() {
    // Initial scrape
    scrapeAllData();
    
    // Scrape every 10 seconds
setInterval(() => {
        scrapeAllData();
    }, 10000);
}

// Initialize the script
function initializeScript() {
    // Add message listener
    safeAddMessageListener();
    
    // Start auto-scraping
    startAutoScrape();
    
    // Also scrape when URL changes (for SPA navigation)
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            setTimeout(scrapeAllData, 1000); // Wait for page to load
        }
    }).observe(document, { subtree: true, childList: true });
    
    // Listen for DOM changes that might indicate new data
    const observer = new MutationObserver((mutations) => {
        let shouldScrape = false;
        
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if new player cards or roster items were added
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const hasPlayerData = node.querySelector && (
                            node.querySelector('.player-rank-item2') ||
                            node.querySelector('.cell.drafted') ||
                            node.querySelector('.cell.current-pick')
                        );
                        
                        if (hasPlayerData) {
                            shouldScrape = true;
                        }
                    }
                });
            }
        });
        
        if (shouldScrape) {
            setTimeout(scrapeAllData, 500);
        }
    });
    
    // Start observing DOM changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Start scraping when page is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeScript);
} else {
    initializeScript();
}

console.log('Fantasy Football Draft Helper: Content script initialized'); 
})(); 