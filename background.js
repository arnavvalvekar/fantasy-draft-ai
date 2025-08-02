// Background service worker for Fantasy Football Draft Helper

console.log('Fantasy Football Draft Helper: Background script loaded');

// Store extension state
let extensionState = {
    isActive: false,
    currentTab: null,
    lastDataUpdate: null,
    dataCache: null
};

// Cache storage for persistent data
let persistentCache = {
    recommendations: {},
    chat: {},
    lastCacheUpdate: null
};

// Initialize cache from storage on startup
chrome.storage.local.get(['persistentCache'], (result) => {
    if (result.persistentCache) {
        persistentCache = result.persistentCache;
        console.log('📦 Loaded persistent cache from storage:', Object.keys(persistentCache.recommendations).length, 'recommendations,', Object.keys(persistentCache.chat).length, 'chat entries');
    }
});

// Save cache to storage periodically
function saveCacheToStorage() {
    chrome.storage.local.set({ persistentCache }, () => {
        console.log('💾 Saved persistent cache to storage');
    });
}

// Cache management functions
function addToCache(cacheType, key, data) {
    const timestamp = Date.now();
    persistentCache[cacheType][key] = {
        data: data,
        timestamp: timestamp
    };
    
    console.log(`⏰ Created cache entry at: ${new Date(timestamp).toLocaleTimeString()}`);
    
    // Clean up old entries (older than 5 minutes)
    const fiveMinutesAgo = timestamp - (5 * 60 * 1000);
    Object.keys(persistentCache[cacheType]).forEach(cacheKey => {
        if (persistentCache[cacheType][cacheKey].timestamp < fiveMinutesAgo) {
            delete persistentCache[cacheType][cacheKey];
        }
    });
    
    persistentCache.lastCacheUpdate = timestamp;
    saveCacheToStorage();
    
    console.log(`💾 Added to ${cacheType} cache:`, key.substring(0, 50) + '...');
    console.log(`📊 Cache size - ${cacheType}:`, Object.keys(persistentCache[cacheType]).length);
}

function getFromCache(cacheType, key) {
    const cacheEntry = persistentCache[cacheType][key];
    if (!cacheEntry) {
        console.log(`❌ Cache miss for ${cacheType}:`, key.substring(0, 50) + '...');
        return null;
    }
    
    // Check if cache is still valid (5 minutes)
    const now = Date.now();
    const fiveMinutesAgo = now - (5 * 60 * 1000);
    const ageInSeconds = (now - cacheEntry.timestamp) / 1000;
    
    console.log(`🔍 Cache entry age: ${ageInSeconds.toFixed(2)} seconds`);
    console.log(`⏰ Cache timestamp: ${new Date(cacheEntry.timestamp).toLocaleTimeString()}`);
    console.log(`⏰ Current time: ${new Date(now).toLocaleTimeString()}`);
    
    if (cacheEntry.timestamp < fiveMinutesAgo) {
        delete persistentCache[cacheType][key];
        saveCacheToStorage();
        console.log(`⏰ Cache expired for ${cacheType}:`, key.substring(0, 50) + '...');
        return null;
    }
    
    console.log(`✅ Cache hit for ${cacheType}:`, key.substring(0, 50) + '...');
    return cacheEntry.data;
}

function clearCache() {
    persistentCache = {
        recommendations: {},
        chat: {},
        lastCacheUpdate: null
    };
    saveCacheToStorage();
    console.log('🗑️ Cleared all persistent cache');
}

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Extension installed:', details.reason);
    
    if (details.reason === 'install') {
        // Set up initial state
        extensionState.isActive = true;
        
        // Open welcome page or show instructions
        chrome.tabs.create({
            url: 'https://sleeper.com'
        });
    }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
    console.log('Extension started');
    extensionState.isActive = true;
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background received message:', message.type);
    
    switch (message.type) {
        case 'DATA_UPDATED':
            // Store updated data from content script
            extensionState.dataCache = message.data;
            extensionState.lastDataUpdate = Date.now();
            
            // Forward to popup if it's open
            chrome.runtime.sendMessage({
                type: 'DATA_UPDATED',
                data: message.data
            }).catch(() => {
                // Popup might not be open, which is fine
            });
            break;
            
        case 'GET_CACHED_DATA':
            // Return cached data to popup
            sendResponse(extensionState.dataCache);
            break;
            
        case 'REQUEST_DATA_SCRAPE':
            // Request fresh data scrape from content script
            if (sender.tab) {
                chrome.tabs.sendMessage(sender.tab.id, {
                    type: 'SCRAPE_NOW'
                }).then(response => {
                    if (response) {
                        extensionState.dataCache = response;
                        extensionState.lastDataUpdate = Date.now();
                        sendResponse(response);
                    } else {
                        sendResponse(null);
                    }
                }).catch(error => {
                    console.error('Error requesting data scrape:', error);
                    sendResponse(null);
                });
            } else {
                sendResponse(null);
            }
            return true; // Keep message channel open for async response
            
        case 'CHECK_TAB_STATUS':
            // Check if current tab is on Sleeper
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                const currentTab = tabs[0];
                const isSleeperTab = currentTab && currentTab.url && 
                                   currentTab.url.includes('sleeper.com');
                
                sendResponse({
                    isSleeperTab,
                    tabUrl: currentTab ? currentTab.url : null
                });
            });
            return true; // Keep message channel open for async response
            
        case 'CACHE_RECOMMENDATION':
            // Cache recommendation data
            addToCache('recommendations', message.key, message.data);
            sendResponse({ success: true });
            break;
            
        case 'GET_CACHED_RECOMMENDATION':
            // Get cached recommendation data
            const cachedRec = getFromCache('recommendations', message.key);
            sendResponse(cachedRec);
            break;
            
        case 'CACHE_CHAT':
            // Cache chat data
            console.log('💾 Caching chat data for key:', message.key.substring(0, 50) + '...');
            addToCache('chat', message.key, message.data);
            sendResponse({ success: true });
            break;
            
        case 'GET_CACHED_CHAT':
            // Get cached chat data
            console.log('🔍 Looking for cached chat with key:', message.key.substring(0, 50) + '...');
            const cachedChat = getFromCache('chat', message.key);
            console.log('📊 Chat cache result:', cachedChat ? 'found' : 'not found');
            sendResponse(cachedChat);
            break;
            
        case 'CLEAR_CACHE':
            // Clear all cache
            clearCache();
            sendResponse({ success: true });
            break;
            
        case 'GET_CACHE_STATS':
            // Get cache statistics
            sendResponse({
                recommendations: Object.keys(persistentCache.recommendations).length,
                chat: Object.keys(persistentCache.chat).length,
                lastUpdate: persistentCache.lastCacheUpdate
            });
            break;
            
        case 'CLEAR_EXPIRED_CHAT':
            // Clear expired chat messages
            const currentTime = Date.now();
            const fiveMinutesAgo = currentTime - (5 * 60 * 1000);
            let clearedCount = 0;
            
            Object.entries(persistentCache.chat).forEach(([key, entry]) => {
                if (entry.timestamp < fiveMinutesAgo) {
                    delete persistentCache.chat[key];
                    clearedCount++;
                }
            });
            
            if (clearedCount > 0) {
                saveCacheToStorage();
                console.log(`🧹 Cleared ${clearedCount} expired chat messages`);
            }
            
            sendResponse({
                cleared: true,
                count: clearedCount
            });
            break;
            
        case 'DEBUG_CACHE':
            // Debug cache contents
            console.log('📊 DEBUG: Full cache contents:');
            console.log('📦 Recommendations cache:', persistentCache.recommendations);
            console.log('📦 Chat cache:', persistentCache.chat);
            console.log('📦 Cache keys:');
            console.log('   - Recommendations:', Object.keys(persistentCache.recommendations));
            console.log('   - Chat:', Object.keys(persistentCache.chat));
            
            // Filter out expired chat messages
            const debugTime = Date.now();
            const debugFiveMinutesAgo = debugTime - (5 * 60 * 1000);
            const validChatEntries = {};
            
            Object.entries(persistentCache.chat).forEach(([key, entry]) => {
                if (entry.timestamp >= debugFiveMinutesAgo) {
                    validChatEntries[key] = entry;
                } else {
                    console.log(`⏰ Removing expired chat entry: ${key.substring(0, 50)}...`);
                    delete persistentCache.chat[key];
                }
            });
            
            // Save updated cache without expired entries
            saveCacheToStorage();
            
            sendResponse({
                recommendations: persistentCache.recommendations,
                chat: validChatEntries,
                keys: {
                    recommendations: Object.keys(persistentCache.recommendations),
                    chat: Object.keys(validChatEntries)
                }
            });
            break;
            
        default:
            console.log('Unknown message type:', message.type);
            sendResponse(null);
    }
});

// Handle tab updates to inject content script when needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && 
        tab.url && 
        tab.url.includes('sleeper.com')) {
        
        console.log('Sleeper tab detected, ensuring content script is active');
        
        // Inject content script if not already present
        chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content.js']
        }).catch(error => {
            console.log('Content script already injected or error:', error);
        });
    }
});

// Handle tab activation
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (tab && tab.url && tab.url.includes('sleeper.com')) {
            extensionState.currentTab = activeInfo.tabId;
            console.log('Active tab is Sleeper:', tab.url);
        }
    });
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    if (tab.url && tab.url.includes('sleeper.com')) {
        // Open popup (this is handled by manifest.json)
        console.log('Extension icon clicked on Sleeper tab');
    } else {
        // Navigate to Sleeper if not already there
        chrome.tabs.update(tab.id, {
            url: 'https://sleeper.com'
        });
    }
});

// Periodic cleanup and maintenance
setInterval(() => {
    // Clean up old cached data (older than 1 hour)
    if (extensionState.lastDataUpdate && 
        Date.now() - extensionState.lastDataUpdate > 3600000) {
        extensionState.dataCache = null;
        console.log('Cleaned up old cached data');
    }
}, 300000); // Check every 5 minutes

// Handle extension errors
chrome.runtime.onSuspend.addListener(() => {
    console.log('Extension suspending');
    extensionState.isActive = false;
});

// Utility function to get current Sleeper tab
async function getCurrentSleeperTab() {
    const tabs = await chrome.tabs.query({ 
        active: true, 
        currentWindow: true 
    });
    
    const currentTab = tabs[0];
    if (currentTab && currentTab.url && currentTab.url.includes('sleeper.com')) {
        return currentTab;
    }
    
    return null;
}

// Export utility functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        extensionState,
        getCurrentSleeperTab
    };
} 