<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlashPaste Pro | Secure Sharing</title>
    
    <!-- Modern Fonts & Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
    
    <!-- Prism is kept for compatibility but content rendering is now restricted -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
</head>
<body>

<nav class="navbar navbar-expand navbar-dark bg-primary sticky-top shadow-sm" role="navigation">
    <div class="container">
        <span class="navbar-brand fw-bold d-flex align-items-center" onclick="location.reload()" style="cursor:pointer" aria-label="FlashPaste Home">
            <span class="me-2">⚡</span> FLASHPASTE PRO
        </span>
        <div class="ms-auto">
            <button class="btn btn-sm btn-outline-light rounded-pill px-3" id="themeToggle" aria-label="Toggle Dark Mode">
                🌓 Appearance
            </button>
        </div>
    </div>
</nav>

<main class="container py-4 py-md-5">
    <!-- CHOICE SCREEN -->
    <div id="choice-screen" class="row g-4 animate-fade-in justify-content-center">
        <div class="col-sm-6 col-lg-5">
            <div class="card border-0 shadow-sm h-100 choice-card" 
                 onclick="showSection('send')" 
                 role="button" 
                 tabindex="0" 
                 onkeypress="if(event.key==='Enter') showSection('send')">
                <div class="card-body p-5 text-center">
                    <div class="display-4 mb-3">📤</div>
                    <h2 class="fw-black h3">SEND</h2>
                    <p class="text-muted small mb-0">Share text or files securely</p>
                </div>
            </div>
        </div>
        <div class="col-sm-6 col-lg-5">
            <div class="card border-0 shadow-sm h-100 choice-card" 
                 onclick="showSection('receive')" 
                 role="button" 
                 tabindex="0" 
                 onkeypress="if(event.key==='Enter') showSection('receive')">
                <div class="card-body p-5 text-center">
                    <div class="display-4 mb-3">📥</div>
                    <h2 class="fw-black h3">RECEIVE</h2>
                    <p class="text-muted small mb-0">Access content via 4-digit code</p>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div id="main-content" class="row g-4 d-none animate-fade-in">
        <div class="col-12 mb-2">
            <button class="btn btn-link text-decoration-none fw-bold p-0 text-primary" onclick="showSection('choice')" aria-label="Go back to main menu">
                ← BACK TO MENU
            </button>
        </div>

        <!-- SEND SECTION -->
        <div id="section-send" class="col-lg-7 mx-auto d-none">
            <div class="card border-0 shadow-sm p-3 p-md-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h5 class="fw-bold m-0">🚀 Create Share</h5>
                    <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="addSnippetInput()">+ Add Text</button>
                </div>
                
                <div id="drop-zone" class="p-4 border-dashed rounded text-center mb-4 bg-body-tertiary">
                    <div class="mb-2 h4">📁</div>
                    <span class="fw-bold">Drop files here</span>
                    <p class="text-muted small mb-0">or click to browse</p>
                    <input type="file" id="fileInput" class="d-none" multiple>
                </div>

                <div id="snippet-container" class="mb-4"></div>

                <div class="form-check form-switch mb-4 p-3 bg-body-tertiary rounded">
                    <input class="form-check-input ms-0 me-3" type="checkbox" id="e2eeToggle" checked>
                    <label class="form-check-label small fw-bold" for="e2eeToggle">🔒 End-to-End Encryption</label>
                </div>

                <button id="generateBtn" class="btn btn-primary w-100 fw-bold py-3 shadow-sm">GENERATE ACCESS CODE</button>
                
                <div id="codeResult" class="mt-4 p-4 bg-primary text-white rounded-4 text-center d-none shadow-lg animate-fade-in">
                    <p class="small text-uppercase ls-2 mb-2 opacity-75">Your Access Code</p>
                    <h1 class="display-2 fw-black mb-0" id="finalCode" style="letter-spacing: 15px; text-indent: 15px;">----</h1>
                </div>
            </div>
        </div>

        <!-- RECEIVE SECTION -->
        <div id="section-receive" class="col-lg-7 mx-auto d-none">
            <div class="card border-0 shadow-sm p-3 p-md-4">
                <h5 class="fw-bold mb-4">🔑 Access Content</h5>
                <div class="input-group mb-4 shadow-sm rounded-pill overflow-hidden">
                    <input type="text" id="accessCode" 
                           class="form-control form-control-lg border-0 text-center ls-5 fw-bold bg-body-tertiary py-3" 
                           placeholder="0000" maxlength="4" 
                           oninput="this.value=this.value.replace(/[^0-9]/g,'')"
                           aria-label="Enter 4 digit code">
                    <button class="btn btn-dark px-4 fw-bold" id="fetchBtn">FETCH</button>
                </div>

                <div id="displayArea" class="d-none">
                    <div class="mb-3 d-flex justify-content-between align-items-center">
                        <small class="text-muted fw-bold">ITEMS FOUND</small>
                    </div>
                    <div id="fetched-snippets"></div>
                </div>

                <div id="welcomeMessage" class="text-center py-5 text-muted bg-body-tertiary rounded-4">
                    <p class="mb-0">Enter the 4-digit code to decrypt and download files.</p>
                </div>
            </div>
        </div>
    </div>
</main>

<script src="script.js"></script>
<script>
    function showSection(type) {
        document.getElementById('choice-screen').classList.toggle('d-none', type !== 'choice');
        document.getElementById('main-content').classList.toggle('d-none', type === 'choice');
        if (type !== 'choice') {
            document.getElementById('section-send').classList.toggle('d-none', type !== 'send');
            document.getElementById('section-receive').classList.toggle('d-none', type !== 'receive');
            
            // Auto-focus input for receive section
            if(type === 'receive') {
                setTimeout(() => document.getElementById('accessCode').focus(), 300);
            }
        }
    }
</script>
</body>
</html>