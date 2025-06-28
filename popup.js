// popup.js

// Example static player ranking (replace with your real list or API)
const playerRanking = [
  "C. McCaffrey", "J. Jefferson", "J. Chase", "T. Hill", "A. Ekeler", "T. Kelce"
];

// Read drafted players from storage when popup opens
chrome.storage.local.get('draftedPlayers', (result) => {
  console.log('Popup read drafted players:', result.draftedPlayers);
  const draftedPlayers = result.draftedPlayers || [];
  updateDraftedPlayers(draftedPlayers);
  updateSuggestion(draftedPlayers);
});

// (Optional) Listen for changes in storage to update UI live if popup is open
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.draftedPlayers) {
    const draftedPlayers = changes.draftedPlayers.newValue || [];
    updateDraftedPlayers(draftedPlayers);
    updateSuggestion(draftedPlayers);
  }
});

// Listen for messages from the content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.draftedPlayers) {
    updateDraftedPlayers(message.draftedPlayers);
    updateSuggestion(message.draftedPlayers);
  }
});

// Update the drafted players list in the UI
function updateDraftedPlayers(players) {
  const ul = document.getElementById('drafted-players');
  ul.innerHTML = '';
  if (players.length === 0) {
    ul.innerHTML = '<li>No players drafted yet.</li>';
    return;
  }
  players.forEach(player => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="pick-number">${player.pickNumber}</span>
                    <span class="player-name">${player.playerName}</span>
                    <span class="position">${player.position}</span>`;
    ul.appendChild(li);
  });
}

// Suggest the top undrafted player
function updateSuggestion(draftedPlayers) {
  const draftedNames = draftedPlayers.map(p => p.playerName);
  const nextPick = playerRanking.find(name => !draftedNames.includes(name));
  document.getElementById('next-pick').textContent = nextPick || "All top players drafted!";
}

// Initial state
updateDraftedPlayers([]);
updateSuggestion([]);

setInterval(() => {
  const draftedPlayers = getDraftedPlayers();
  console.log('Drafted players:', draftedPlayers);
  chrome.storage.local.set({ draftedPlayers });
}, 2000);