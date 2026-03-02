<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlashPaste Pro | Any File & Code Sharing</title>
    
    <!-- PWA Blob Manifest -->
    <script id="pwa-manifest">
        const base = window.location.origin + window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/') + 1);
        const manifest = {
            "name": "FlashPaste Pro",
            "short_name": "FlashPaste",
            "description": "Secure, binary file and code clipboard with E2EE.",
            "start_url": window.location.href,
            "display": "standalone",
            "background_color": "#0d6efd",
            "theme_color": "#0d6efd",
            "icons": [
                {"src": base + "logo-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                {"src": base + "logo-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"}
            ]
        };
        const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
        const link = document.createElement('link');
        link.rel = 'manifest'; link.href = URL.createObjectURL(blob);
        document.head.appendChild(link);
    </script>
    <link rel="icon" type="image/png" href="logo-192.png">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
</head>
<body>

<nav class="navbar navbar-expand navbar-dark bg-primary sticky-top shadow-sm">
    <div class="container">
        <span class="navbar-brand fw-bold" onclick="location.reload()" style="cursor:pointer">⚡ FLASH<span class="opacity-75">PASTE</span> PRO</span>
        <div class="ms-auto d-flex align-items-center">
            <button class="btn btn-sm btn-outline-light me-3" id="themeToggle">🌓 Mode</button>
            <span class="badge bg-white text-primary d-none d-sm-inline">V2.0 Files</span>
        </div>
    </div>
</nav>

<div class="container py-4">
    <!-- CHOICE SECTION -->
    <div id="choice-screen" class="row g-4 full-height-choice animate-fade-in">
        <div class="col-md-6">
            <div class="card border-0 shadow-sm p-5 text-center choice-card" onclick="showSection('send')">
                <div class="choice-icon">📤</div>
                <h2 class="fw-black text-primary">SEND</h2>
                <p class="text-muted">Upload any file or paste code snippets.</p>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card border-0 shadow-sm p-5 text-center choice-card" onclick="showSection('receive')">
                <div class="choice-icon">📥</div>
                <h2 class="fw-black text-dark">RECEIVE</h2>
                <p class="text-muted">Enter code to download shared files/text.</p>
            </div>
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div id="main-content" class="row g-4 d-none animate-fade-in">
        <div class="col-12 mb-2">
            <a class="text-primary back-btn fw-bold" onclick="showSection('choice')">← Back to Menu</a>
        </div>

        <div id="section-send" class="col-lg-8 mx-auto d-none">
            <div class="card border-0 shadow-sm p-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0 fw-bold">🚀 Share Anything</h5>
                    <button class="btn btn-sm btn-primary" onclick="addSnippetInput()">+ Add Text</button>
                </div>

                <div id="drop-zone" class="p-4 border-dashed rounded text-center mb-3 text-muted bg-light">
                    <b>DROP FILES HERE</b><br>
                    <small>Images, PDF, Word, PPT, Code - everything allowed</small>
                    <input type="file" id="fileInput" class="d-none" multiple>
                </div>
                
                <div id="snippet-container" class="mb-3"></div>

                <div class="row g-2">
                    <div class="col-md-6">
                        <div class="form-check form-switch p-2 border rounded">
                            <input class="form-check-input ms-0 me-2" type="checkbox" id="e2eeToggle" checked>
                            <label class="form-check-label small fw-bold" for="e2eeToggle">🔒 End-to-End Encryption</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <button id="generateBtn" class="btn btn-primary w-100 fw-bold py-2 shadow-sm">GENERATE CODE</button>
                    </div>
                </div>

                <div id="codeResult" class="mt-4 p-4 bg-primary text-white rounded text-center d-none animate-fade-in shadow">
                    <p class="small mb-1 text-uppercase ls-2">Access Code</p>
                    <h1 class="display-1 fw-bold mb-0" id="finalCode">----</h1>
                    <div class="mt-2 x-small opacity-75">Data expires in 10 minutes.</div>
                </div>
            </div>
        </div>

        <div id="section-receive" class="col-lg-8 mx-auto d-none">
            <div class="card border-0 shadow-sm p-4">
                <h5 class="fw-bold">🔑 Access Files</h5>
                <div class="input-group my-3">
                    <input type="text" id="accessCode" class="form-control form-control-lg text-center ls-5 fw-bold" placeholder="0000" maxlength="8">
                    <button class="btn btn-dark px-4 fw-bold" id="fetchBtn">FETCH</button>
                </div>
                <div id="displayArea" class="d-none"><div id="fetched-snippets"></div></div>
                <div id="welcomeMessage" class="text-center py-5 text-muted border-top">
                    <p class="small">Enter the 4-digit code to begin download.</p>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="script.js"></script>
<script>
    function showSection(type) {
        document.getElementById('choice-screen').classList.toggle('d-none', type !== 'choice');
        document.getElementById('main-content').classList.toggle('d-none', type === 'choice');
        if (type !== 'choice') {
            document.getElementById('section-send').classList.toggle('d-none', type !== 'send');
            document.getElementById('section-receive').classList.toggle('d-none', type !== 'receive');
        }
    }
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => { navigator.serviceWorker.register('sw.js'); });
    }
</script>
</body>
</html>