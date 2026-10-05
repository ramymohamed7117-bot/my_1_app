let deferredPrompt = null;
const installBtn = document.getElementById('installAppBtn');
const installBtnMobile = document.getElementById('installAppBtnMobile');

function showInstallButtons(show) {
  if (installBtn) installBtn.classList.toggle('d-none', !show);
  if (installBtnMobile) installBtnMobile.classList.toggle('show-btn', show);
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButtons(true);
});

async function installPWA() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  showInstallButtons(false);
}

if (installBtn) installBtn.addEventListener('click', installPWA);
if (installBtnMobile) installBtnMobile.addEventListener('click', installPWA);

window.addEventListener('appinstalled', () => {
  deferredPrompt = null;
  showInstallButtons(false);
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => console.log('SW registration failed', err));
  });
}
