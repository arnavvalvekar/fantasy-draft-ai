console.log("DraftBuilder AI content script loaded!");
// You can add code here to interact with the page 

// Only run if not already injected
if (!document.getElementById('draftbuilder-ai-banner')) {
  const banner = document.createElement('div');
  banner.id = 'draftbuilder-ai-banner';
  banner.textContent = 'BIG BLACK BALLS! BIG BLACK BALLS! BIG BLACK BALLS!';
  banner.style.position = 'fixed';
  banner.style.top = '0';
  banner.style.left = '0';
  banner.style.width = '100%';
  banner.style.background = '#4CAF50';
  banner.style.color = 'white';
  banner.style.textAlign = 'center';
  banner.style.padding = '10px';
  banner.style.zIndex = '9999';
  document.body.appendChild(banner);
}

function getDraftedPlayers() {
  // Find all elements that represent a draft pick row
  // You may need to adjust the parent selector if these are grouped in a container
  const pickElements = document.querySelectorAll('.pick');

  const draftedPlayers = Array.from(pickElements).map(pickEl => {
    // The parent of .pick should contain the other info
    const parent = pickEl.parentElement;

    const playerName = parent.querySelector('.player-name')?.textContent.trim() || '';
    const position = parent.querySelector('.position')?.textContent.trim() || '';
    const pickNumber = pickEl.textContent.trim();

    return {
      pickNumber,
      playerName,
      position
    };
  });

  return draftedPlayers;
}

// Example: Log drafted players every 2 seconds
setInterval(() => {
  const draftedPlayers = getDraftedPlayers();
  console.log('Drafted players:', draftedPlayers);
  // TODO: Send this data to your popup or background script
}, 2000); 