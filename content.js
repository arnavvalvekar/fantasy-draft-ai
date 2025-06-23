console.log("DraftBuilder AI content script loaded!");
// You can add code here to interact with the page 

// Only run if not already injected
if (!document.getElementById('draftbuilder-ai-banner')) {
  const banner = document.createElement('div');
  banner.id = 'draftbuilder-ai-banner';
  banner.textContent = 'DraftBuilder AI is active on this draft page!';
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