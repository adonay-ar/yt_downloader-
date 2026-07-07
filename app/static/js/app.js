document.addEventListener('DOMContentLoaded', () => {
    // UI Elements - Tabs
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    // UI Elements - Fetch Video Info
    const videoUrlInput = document.getElementById('video-url');
    const btnFetch = document.getElementById('btn-fetch');
    const fetchText = document.getElementById('fetch-text');
    const fetchSpinner = document.getElementById('fetch-spinner');
    
    // UI Elements - Video Card
    const videoCard = document.getElementById('video-card');
    const consoleEmptyState = document.getElementById('console-empty-state');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoDuration = document.getElementById('video-duration');
    const videoTitle = document.getElementById('video-title');
    const videoChannel = document.getElementById('video-channel');
    const videoViews = document.getElementById('video-views');
    const formatSelect = document.getElementById('format-select');
    const btnDownload = document.getElementById('btn-download');

    // UI Elements - Progress
    const downloadProgressContainer = document.getElementById('download-progress-container');
    const downloadEmptyState = document.getElementById('download-empty-state');
    const progressFilename = document.getElementById('progress-filename');
    const progressPercent = document.getElementById('progress-percent');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressSpeed = document.getElementById('progress-speed');
    const progressEta = document.getElementById('progress-eta');
    const progressStatusMsg = document.getElementById('progress-status-msg');

    // UI Elements - Files List
    const downloadedList = document.getElementById('downloaded-list');
    const filesEmptyState = document.getElementById('files-empty-state');
    const btnRefreshFiles = document.getElementById('btn-refresh-files');
    const btnClear = document.getElementById('btn-clear');

    // UI Elements - OAuth2
    const btnStartOauth = document.getElementById('btn-start-oauth');
    const oauthPromptContainer = document.getElementById('oauth-prompt-container');
    const oauthLink = document.getElementById('oauth-link');
    const oauthCode = document.getElementById('oauth-code');
    const btnCopyOauthCode = document.getElementById('btn-copy-oauth-code');

    // UI Elements - Cookies
    const cookieBadge = document.getElementById('cookie-badge');
    const cookieInfoText = document.getElementById('cookie-info-text');
    const btnDeleteCookie = document.getElementById('btn-delete-cookie');
    const cookieDropzone = document.getElementById('cookie-dropzone');
    const cookieFileInput = document.getElementById('cookie-file-input');

    // UI Elements - Toast
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastMessage = document.getElementById('toast-message');

    // UI Elements - Updates
    const appVersionVal = document.getElementById('app-version-val');
    const lblCurrentVersion = document.getElementById('lbl-current-version');
    const lblUpdateStatus = document.getElementById('lbl-update-status');
    const btnCheckUpdatesPanel = document.getElementById('btn-check-updates-panel');
    const btnMockUpdate = document.getElementById('btn-mock-update');
    const updateDetailsContainer = document.getElementById('update-details-container');
    const lblNewVersion = document.getElementById('lbl-new-version');
    const lblReleaseNotes = document.getElementById('lbl-release-notes');
    const btnInstallUpdate = document.getElementById('btn-install-update');
    const updateInstallingContainer = document.getElementById('update-installing-container');
    const lnkCheckUpdate = document.getElementById('lnk-check-update');
    const lblInstallingText = document.getElementById('lbl-installing-text');

    // State Variables
    let currentVideoUrl = '';
    let socket = null;
    let pendingUpdateData = null;

    /* ==========================================
       TAB MANAGEMENT
       ========================================== */
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const targetTab = link.getAttribute('data-tab');
            
            // Remove active classes
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and its content
            link.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    function switchTab(tabId) {
        const link = document.querySelector(`.tab-link[data-tab="${tabId}"]`);
        if (link) link.click();
    }

    /* ==========================================
       TOAST NOTIFICATIONS
       ========================================== */
    function showToast(message, type = 'info') {
        toastMessage.textContent = message;
        toast.className = 'toast'; // Reset
        
        if (type === 'success') {
            toast.classList.add('toast-success');
            toastIcon.className = 'fa-solid fa-circle-check';
        } else if (type === 'danger') {
            toast.classList.add('toast-danger');
            toastIcon.className = 'fa-solid fa-circle-exclamation';
        } else {
            toastIcon.className = 'fa-solid fa-circle-info';
        }
        
        toast.classList.remove('hidden');
        
        // Hide after 4 seconds
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 4000);
    }

    /* ==========================================
       WEBSOCKET CONNECTION
       ========================================== */
    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/download`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connected to', wsUrl);
        };

        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            
            if (msg.type === 'download_progress') {
                const data = msg.data;
                handleDownloadProgress(data);
            } 
            else if (msg.type === 'oauth_status') {
                const data = msg.data;
                handleOauthStatus(data);
            }
            else if (msg.type === 'error') {
                showToast(`Error: ${msg.message}`, 'danger');
            }
        };

        socket.onclose = () => {
            console.log('WebSocket connection closed. Reconnecting in 3s...');
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }

    // Connect initially
    connectWebSocket();

    /* ==========================================
       FETCH VIDEO INFO
       ========================================== */
    btnFetch.addEventListener('click', async () => {
        const url = videoUrlInput.value.trim();
        if (!url) {
            showToast('Por favor, ingresa un enlace de YouTube válido.', 'danger');
            return;
        }

        // Set Loading State
        btnFetch.disabled = true;
        fetchText.classList.add('hidden');
        fetchSpinner.classList.remove('hidden');
        
        // Reset Video Card
        videoCard.classList.add('hidden');
        consoleEmptyState.classList.remove('hidden');

        try {
            const response = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                currentVideoUrl = url;
                
                // Populate UI Card
                videoThumbnail.src = data.thumbnail;
                videoDuration.textContent = data.duration;
                videoTitle.textContent = data.title;
                videoChannel.innerHTML = `<i class="fa-solid fa-user-circle"></i> ${data.channel}`;
                videoViews.innerHTML = `<i class="fa-solid fa-eye"></i> ${data.views.toLocaleString()} vistas`;
                
                // Clear and Populate formats
                formatSelect.innerHTML = '';
                data.formats.forEach(fmt => {
                    const option = document.createElement('option');
                    option.value = fmt.id;
                    option.textContent = `${fmt.resolution} - ${fmt.note}`;
                    formatSelect.appendChild(option);
                });

                // Display Video Card
                consoleEmptyState.classList.add('hidden');
                videoCard.classList.remove('hidden');
                showToast('Información cargada correctamente.', 'success');
            } else {
                showToast(data.error || 'No se pudo cargar la información del video.', 'danger');
            }
        } catch (err) {
            console.error(err);
            showToast('Ocurrió un error al conectar con el servidor.', 'danger');
        } finally {
            // Restore Button State
            btnFetch.disabled = false;
            fetchText.classList.remove('hidden');
            fetchSpinner.classList.add('hidden');
        }
    });

    /* ==========================================
       DOWNLOAD TRIGGERS
       ========================================== */
    btnDownload.addEventListener('click', () => {
        if (!currentVideoUrl || !socket || socket.readyState !== WebSocket.OPEN) {
            showToast('Error: Conexión WebSocket no lista o URL no cargada.', 'danger');
            return;
        }

        const formatId = formatSelect.value;
        
        // Send down message via socket
        socket.send(JSON.stringify({
            type: 'start_download',
            url: currentVideoUrl,
            format_id: formatId
        }));

        // Switch to status progress tab
        switchTab('tab-downloads');
        showToast('Descarga iniciada...', 'info');
    });

    function handleDownloadProgress(data) {
        if (data.status === 'starting') {
            downloadEmptyState.classList.add('hidden');
            downloadProgressContainer.classList.remove('hidden');
            
            progressFilename.textContent = 'Inicializando descarga...';
            progressPercent.textContent = '0%';
            progressBarFill.style.width = '0%';
            progressSpeed.textContent = '-';
            progressEta.textContent = '-';
            progressStatusMsg.textContent = data.message;
        }
        else if (data.status === 'downloading') {
            downloadEmptyState.classList.add('hidden');
            downloadProgressContainer.classList.remove('hidden');

            progressFilename.textContent = data.filename || 'Descargando...';
            progressPercent.textContent = `${data.percent}%`;
            progressBarFill.style.width = `${data.percent}%`;
            progressSpeed.textContent = data.speed || '-';
            progressEta.textContent = data.eta || '-';
            progressStatusMsg.textContent = `Descargando archivo...`;
        }
        else if (data.status === 'merging') {
            progressBarFill.style.width = '100%';
            progressPercent.textContent = '99%';
            progressStatusMsg.textContent = data.message || 'Procesando capas de video/audio...';
        }
        else if (data.status === 'completed') {
            showToast('¡Descarga completada con éxito!', 'success');
            resetDownloadProgress();
            loadDownloadedFiles();
            switchTab('tab-files');
        }
        else if (data.status === 'failed') {
            showToast(`La descarga falló: ${data.error}`, 'danger');
            resetDownloadProgress();
        }
    }

    function resetDownloadProgress() {
        downloadProgressContainer.classList.add('hidden');
        downloadEmptyState.classList.remove('hidden');
    }

    /* ==========================================
       DOWNLOADED FILES MANAGEMENT
       ========================================== */
    async function loadDownloadedFiles() {
        try {
            const response = await fetch('/api/downloads/list');
            if (response.ok) {
                const files = await response.json();
                downloadedList.innerHTML = '';
                
                if (files.length === 0) {
                    filesEmptyState.classList.remove('hidden');
                } else {
                    filesEmptyState.classList.add('hidden');
                    files.forEach(file => {
                        const li = document.createElement('li');
                        li.className = 'downloaded-item';
                        li.innerHTML = `
                            <div class="file-info">
                                <span class="file-name" title="${file.name}">${file.name}</span>
                                <span class="file-size"><i class="fa-solid fa-hard-drive"></i> ${file.size}</span>
                            </div>
                            <div style="display: flex; gap: 0.4rem; align-items: center;">
                                <a href="${file.path}" download class="btn btn-sm btn-icon" title="Descargar al navegador">
                                    <i class="fa-solid fa-circle-down"></i>
                                </a>
                                <button class="btn btn-sm btn-danger btn-icon btn-delete-file" title="Eliminar del servidor">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        `;
                        const btnDelete = li.querySelector('.btn-delete-file');
                        btnDelete.addEventListener('click', () => {
                            deleteFile(file.name);
                        });
                        downloadedList.appendChild(li);
                    });
                }
            }
        } catch (err) {
            console.error('Error loading downloads list:', err);
        }
    }

    async function deleteFile(filename) {
        if (!confirm(`¿Estás seguro de que deseas eliminar permanentemente el archivo "${filename}" del servidor?`)) {
            return;
        }
        try {
            const response = await fetch(`/api/downloads/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (response.ok && data.success) {
                showToast(data.message, 'success');
                loadDownloadedFiles();
            } else {
                showToast(data.detail || 'Error al eliminar el archivo.', 'danger');
            }
        } catch (err) {
            console.error('Error deleting file:', err);
            showToast('Error al conectar con el servidor para eliminar el archivo.', 'danger');
        }
    }

    btnClear.addEventListener('click', () => {
        videoUrlInput.value = '';
        videoCard.classList.add('hidden');
        consoleEmptyState.classList.remove('hidden');
        currentVideoUrl = '';
        showToast('Listo para una nueva descarga.', 'info');
    });

    btnRefreshFiles.addEventListener('click', loadDownloadedFiles);
    // Load files initially
    loadDownloadedFiles();

    /* ==========================================
       OAUTH2 FLOW
       ========================================== */
    btnStartOauth.addEventListener('click', () => {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            showToast('Error: Conexión con el servidor no disponible.', 'danger');
            return;
        }

        socket.send(JSON.stringify({
            type: 'start_oauth2'
        }));
        
        btnStartOauth.disabled = true;
    });

    function handleOauthStatus(data) {
        if (data.type === 'oauth_started') {
            oauthPromptContainer.classList.remove('hidden');
            oauthCode.textContent = 'Cargando...';
            oauthLink.href = '#';
            showToast(data.message, 'info');
        }
        else if (data.type === 'oauth_prompt') {
            oauthPromptContainer.classList.remove('hidden');
            oauthCode.textContent = data.code;
            oauthLink.href = data.url;
            oauthLink.innerHTML = `${data.url} <i class="fa-solid fa-external-link"></i>`;
            
            showToast('Código de dispositivo generado. Regístralo en Google.', 'info');
        }
        else if (data.type === 'oauth_success') {
            showToast(data.message, 'success');
            oauthPromptContainer.classList.add('hidden');
            btnStartOauth.disabled = false;
        }
        else if (data.type === 'oauth_failed') {
            showToast(data.message, 'danger');
            oauthPromptContainer.classList.add('hidden');
            btnStartOauth.disabled = false;
        }
        else if (data.type === 'oauth_finished') {
            btnStartOauth.disabled = false;
        }
    }

    btnCopyOauthCode.addEventListener('click', () => {
        const code = oauthCode.textContent;
        if (code && code !== 'Cargando...') {
            navigator.clipboard.writeText(code)
                .then(() => {
                    showToast('Código copiado al portapapeles.', 'success');
                })
                .catch(err => {
                    console.error('Could not copy text: ', err);
                });
        }
    });

    /* ==========================================
       COOKIES MANAGEMENT
       ========================================== */
    async function checkCookieStatus() {
        try {
            const response = await fetch('/api/cookies/status');
            if (response.ok) {
                const data = await response.json();
                if (data.active) {
                    cookieBadge.className = 'cookie-badge active';
                    cookieBadge.textContent = 'Activo';
                    cookieInfoText.textContent = `Archivo cookies.txt cargado (${data.size})`;
                    btnDeleteCookie.classList.remove('hidden');
                } else {
                    cookieBadge.className = 'cookie-badge inactive';
                    cookieBadge.textContent = 'Inactivo';
                    cookieInfoText.textContent = 'No se ha cargado ningún archivo de cookies';
                    btnDeleteCookie.classList.add('hidden');
                }
            }
        } catch (err) {
            console.error('Error checking cookie status:', err);
        }
    }

    // Delete cookies trigger
    btnDeleteCookie.addEventListener('click', async () => {
        if (confirm('¿Estás seguro de que quieres eliminar el archivo de cookies activo?')) {
            try {
                const response = await fetch('/api/cookies', { method: 'DELETE' });
                const data = await response.json();
                if (response.ok && data.success) {
                    showToast(data.message, 'success');
                    checkCookieStatus();
                } else {
                    showToast(data.message || 'Error al eliminar cookies.', 'danger');
                }
            } catch (err) {
                console.error(err);
                showToast('Error al conectar con el servidor.', 'danger');
            }
        }
    });

    // Dropzone Events
    cookieDropzone.addEventListener('click', () => cookieFileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        cookieDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            cookieDropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        cookieDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            cookieDropzone.classList.remove('dragover');
        }, false);
    });

    cookieDropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            handleCookieUpload(files[0]);
        }
    });

    cookieFileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleCookieUpload(e.target.files[0]);
        }
    });

    async function handleCookieUpload(file) {
        if (!file.name.endsWith('.txt')) {
            showToast('Por favor, sube un archivo de texto (.txt) válido.', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/cookies', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok && data.success) {
                showToast(data.message, 'success');
                checkCookieStatus();
            } else {
                showToast(data.detail || 'Error al subir archivo de cookies.', 'danger');
            }
        } catch (err) {
            console.error(err);
            showToast('Error al conectar con el servidor para la carga de cookies.', 'danger');
        }
    }

    /* ==========================================
       SYSTEM UPDATES LOGIC
       ========================================== */
    async function fetchVersion() {
        try {
            const response = await fetch('/api/update/version');
            if (response.ok) {
                const data = await response.json();
                appVersionVal.textContent = data.version;
                lblCurrentVersion.textContent = `v${data.version}`;
            }
        } catch (err) {
            console.error('Error fetching version:', err);
        }
    }

    async function checkUpdates(isManual = false) {
        if (isManual) {
            showToast('Buscando actualizaciones...', 'info');
            btnCheckUpdatesPanel.disabled = true;
        }

        try {
            const response = await fetch('/api/update/check');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    if (data.update_available) {
                        pendingUpdateData = {
                            zip_url: data.zip_url,
                            version: data.remote_version
                        };
                        
                        // Show update box
                        lblNewVersion.textContent = `v${data.remote_version}`;
                        lblReleaseNotes.textContent = data.release_notes;
                        updateDetailsContainer.classList.remove('hidden');
                        
                        // Update status badge
                        lblUpdateStatus.className = 'update-status-badge status-alert';
                        lblUpdateStatus.textContent = 'Actualización Disponible';
                        
                        showToast(`¡Nueva versión v${data.remote_version} disponible!`, 'info');
                    } else {
                        pendingUpdateData = null;
                        updateDetailsContainer.classList.add('hidden');
                        
                        // Update status badge
                        lblUpdateStatus.className = 'update-status-badge status-ok';
                        lblUpdateStatus.textContent = 'Al día';
                        
                        if (isManual) {
                            showToast('La aplicación ya está actualizada a la última versión.', 'success');
                        }
                    }
                } else {
                    if (isManual) showToast(`Error al comprobar: ${data.error}`, 'danger');
                }
            }
        } catch (err) {
            console.error('Error checking updates:', err);
            if (isManual) showToast('Error al conectar con el servidor de actualizaciones.', 'danger');
        } finally {
            if (isManual) btnCheckUpdatesPanel.disabled = false;
        }
    }

    // Trigger mock update configurations for local user validation
    btnMockUpdate.addEventListener('click', async () => {
        showToast('Simulando búsqueda de actualización...', 'info');
        btnMockUpdate.disabled = true;
        
        try {
            const response = await fetch('/api/update/mock-config');
            if (response.ok) {
                const data = await response.json();
                pendingUpdateData = {
                    zip_url: data.zip_url,
                    version: data.version
                };
                
                // Show update details
                lblNewVersion.textContent = `v${data.version}`;
                lblReleaseNotes.textContent = data.release_notes;
                updateDetailsContainer.classList.remove('hidden');
                
                // Update badge
                lblUpdateStatus.className = 'update-status-badge status-alert';
                lblUpdateStatus.textContent = 'Actualización Disponible (Simulada)';
                
                showToast(`Simulación completada. Nueva versión v${data.version} disponible para instalar.`, 'success');
                switchTab('tab-update');
            }
        } catch (err) {
            console.error('Error in mock update:', err);
            showToast('Error al simular actualización.', 'danger');
        } finally {
            btnMockUpdate.disabled = false;
        }
    });

    btnCheckUpdatesPanel.addEventListener('click', () => checkUpdates(true));

    lnkCheckUpdate.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab('tab-update');
        checkUpdates(true);
    });

    btnInstallUpdate.addEventListener('click', async () => {
        if (!pendingUpdateData) return;
        
        if (!confirm(`¿Deseas descargar e instalar la versión ${pendingUpdateData.version} de la aplicación?\nEl contenedor Docker se reiniciará automáticamente.`)) {
            return;
        }

        btnInstallUpdate.disabled = true;
        updateDetailsContainer.classList.add('hidden');
        updateInstallingContainer.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/update/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pendingUpdateData)
            });

            const data = await response.json();
            if (response.ok && data.success) {
                lblInstallingText.textContent = 'Instalado con éxito. Reiniciando...';
                showToast('Actualización descargada. Esperando reinicio de contenedor...', 'success');
                
                // Start polling to detect when the container recovers
                startReconnectPoll();
            } else {
                showToast(data.error || 'La instalación falló.', 'danger');
                updateInstallingContainer.classList.add('hidden');
                updateDetailsContainer.classList.remove('hidden');
                btnInstallUpdate.disabled = false;
            }
        } catch (err) {
            console.error('Error installing update:', err);
            // Since Uvicorn exits, it might drop the socket/fetch connection with a network error.
            // In case of a premature connection close, we still poll to see if it recovered!
            lblInstallingText.textContent = 'Aplicando cambios...';
            showToast('Conexión reiniciada para aplicar actualización...', 'info');
            startReconnectPoll();
        }
    });

    function startReconnectPoll() {
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            try {
                // Try fetching a light endpoint to verify server is back
                const res = await fetch('/api/update/version');
                if (res.ok) {
                    clearInterval(interval);
                    showToast('¡Aplicación reconectada y actualizada con éxito!', 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } catch (e) {
                console.log(`Buscando conexión... intento ${attempts}`);
            }
        }, 2000);
    }

    // Check cookie status on load
    checkCookieStatus();
    // Load app version details
    fetchVersion();
});
