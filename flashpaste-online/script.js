let snippetCount = 0;

window.onload = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code) {
        document.getElementById('accessCode').value = code;
        showSection('receive');
        setTimeout(() => document.getElementById('fetchBtn').click(), 500);
    }
};

document.getElementById('themeToggle').onclick = () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-bs-theme');
    const target = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', target);
};

// Binary Handlers
function uint8ToBase64(u8Arr) {
    let CHUNK_SIZE = 0x8000; let index = 0; let result = '';
    while (index < u8Arr.length) {
        result += String.fromCharCode.apply(null, u8Arr.subarray(index, index + CHUNK_SIZE));
        index += CHUNK_SIZE;
    }
    return btoa(result);
}
function base64ToUint8(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
}

// UI: Add Inputs
function addSnippetInput(initialValue = '', fileName = '', fileType = 'text') {
    snippetCount++;
    const container = document.getElementById('snippet-container');
    const div = document.createElement('div');
    div.className = "mb-3 p-3 bg-body-secondary border rounded-4 position-relative animate-fade-in shadow-sm";
    const isFile = fileType === 'file';
    div.innerHTML = `
        <div class="d-flex justify-content-between mb-2">
            <span class="badge ${isFile ? 'bg-primary' : 'bg-secondary'} rounded-pill px-3">${isFile ? '📎 FILE' : '📄 TEXT'}</span>
            <button class="btn-close" onclick="this.parentElement.parentElement.remove()" aria-label="Remove item"></button>
        </div>
        ${isFile ? `
            <div class="p-3 text-center border rounded-3 bg-white text-dark shadow-sm">
                <div class="fw-bold text-truncate" title="${fileName}">${fileName}</div>
                <input type="hidden" class="snippet-input" data-filename="${fileName}" data-type="file" value="${initialValue}">
            </div>
        ` : `
            <textarea class="form-control snippet-input mb-2 border-0 shadow-none" rows="3" data-type="text" placeholder="Paste your text here...">${initialValue}</textarea>
            <div class="d-flex align-items-center">
                <small class="text-muted me-2 small fw-bold">LANG:</small>
                <select class="form-select form-select-sm language-select border-0 bg-transparent w-auto py-0 shadow-none">
                    <option value="text">Plain Text</option>
                    <option value="javascript">JavaScript</option>
                    <option value="markdown">Markdown</option>
                    <option value="python">Python</option>
                    <option value="html">HTML</option>
                </select>
            </div>
        `}
    `;
    container.appendChild(div);
}

// File Drop
const fileInput = document.getElementById('fileInput');
document.getElementById('drop-zone').onclick = () => fileInput.click();
fileInput.onchange = (e) => {
    for (const file of e.target.files) {
        const reader = new FileReader();
        reader.onload = (ev) => addSnippetInput(ev.target.result.split(',')[1], file.name, 'file');
        reader.readAsDataURL(file);
    }
};

// Crypto
async function deriveKey(passcode) {
    const encoder = new TextEncoder();
    const salt = encoder.encode('flashpaste-salt-v2');
    const baseKey = await crypto.subtle.importKey('raw', encoder.encode(passcode), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
        baseKey, { name: 'AES-GCM', length: 256 }, false, ['encrypt','decrypt']
    );
}
async function encryptData(text, code) {
    const key = await deriveKey(code);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(text));
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv); combined.set(new Uint8Array(ciphertext), iv.length);
    return uint8ToBase64(combined);
}
async function decryptData(base64, code) {
    try {
        const key = await deriveKey(code);
        const combined = base64ToUint8(base64);
        const decrypted = await crypto.subtle.decrypt({ name:'AES-GCM', iv: combined.slice(0,12) }, key, combined.slice(12));
        return new TextDecoder().decode(decrypted);
    } catch(e) { return null; }
}

// ACTION: SEND
document.getElementById('generateBtn').onclick = async () => {
    const inputs = document.querySelectorAll('.snippet-input');
    const langs = document.querySelectorAll('.language-select');
    let snippets = [];
    inputs.forEach((input, i) => {
        if(input.value) {
            snippets.push({
                content: input.value,
                name: input.getAttribute('data-filename') || 'text.txt',
                type: input.getAttribute('data-type'),
                lang: langs[i]?.value || 'text'
            });
        }
    });

    if(!snippets.length) return;
    
    const code = Math.floor(1000 + Math.random() * 9000).toString();
    const encrypted = document.getElementById('e2eeToggle').checked;
    let payload = JSON.stringify(snippets);
    if(encrypted) payload = await encryptData(payload, code);

    const fd = new FormData();
    fd.append('content', payload);
    fd.append('code', code);
    fd.append('encrypted', encrypted ? 'true' : 'false');

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerText = "PROCESSING...";

    try {
        const res = await fetch('api.php?action=save', { method: 'POST', body: fd });
        const data = await res.json();
        if(data.success) {
            document.getElementById('finalCode').innerText = data.code;
            document.getElementById('codeResult').classList.remove('d-none');
            btn.innerText = "SUCCESS ✅";
        }
    } catch(e) { 
        btn.disabled = false;
        btn.innerText = "GENERATE ACCESS CODE";
    }
};

// ACTION: FETCH (IMPROVED UI - NO CONTENT DISTORTION)
document.getElementById('fetchBtn').onclick = async () => {
    const code = document.getElementById('accessCode').value.trim();
    if(code.length !== 4) return;
    const btn = document.getElementById('fetchBtn');
    btn.disabled = true;
    btn.innerText = "⌛";

    try {
        const res = await fetch(`api.php?action=fetch&code=${code}`);
        const data = await res.json();
        if(!data.success) { 
            btn.innerText = "FETCH";
            btn.disabled = false; 
            return; 
        }

        let payload = data.content;
        if(data.encrypted) payload = await decryptData(payload, code);
        if(!payload) { 
            btn.innerText = "FETCH";
            btn.disabled = false; 
            return; 
        }

        displaySnippets(JSON.parse(payload));
        document.getElementById('displayArea').classList.remove('d-none');
        document.getElementById('welcomeMessage').classList.add('d-none');
    } catch(e) { 
        btn.innerText = "FETCH";
    }
    btn.disabled = false;
    btn.innerText = "FETCH";
};

/**
 * FIXED UI: Shows Snippet Number only.
 * No content rendering to prevent "distortion".
 */
function displaySnippets(snippets) {
    const container = document.getElementById('fetched-snippets');
    container.innerHTML = '';
    
    snippets.forEach((s, index) => {
        const card = document.createElement('div');
        card.className = "card mb-3 border-0 shadow-sm overflow-hidden animate-fade-in";
        
        const isFile = s.type === 'file';
        
        card.innerHTML = `
            <div class="card-body bg-body-secondary py-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center me-3 min-w-0">
                        <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center fw-bold me-3" style="width:36px; height:36px; min-width:36px;">
                            ${index + 1}
                        </div>
                        <div class="text-truncate">
                            <small class="text-uppercase text-muted d-block fw-bold" style="font-size:10px">
                                ${isFile ? 'ATTACHMENT' : `SNIPPET (${s.lang.toUpperCase()})`}
                            </small>
                            <strong class="text-body text-truncate d-block" style="max-width:200px">
                                ${isFile ? s.name : 'Shared Text Content'}
                            </strong>
                        </div>
                    </div>
                    <div>
                        ${isFile ? 
                            `<button class="btn btn-primary btn-sm px-4 rounded-pill fw-bold" onclick="downloadFile('${s.content}', '${s.name}')">DOWNLOAD</button>` : 
                            `<button class="btn btn-dark btn-sm px-4 rounded-pill fw-bold" onclick="copySnippet(this, \`${s.content.replace(/`/g, '\\`').replace(/\${/g, '\\${')}\`)">COPY</button>`
                        }
                    </div>
                </div>
            </div>`;
        
        container.appendChild(card);
    });
}

function downloadFile(b64, name) {
    const a = document.createElement('a');
    a.href = `data:application/octet-stream;base64,${b64}`;
    a.download = name; a.click();
}

function copySnippet(btn, txt) {
    const originalText = btn.innerText;
    // Use clipboard API or fallback
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(txt).then(() => {
            btn.innerText = "COPIED!";
            btn.classList.replace('btn-dark', 'btn-success');
            setTimeout(() => {
                btn.innerText = originalText;
                btn.classList.replace('btn-success', 'btn-dark');
            }, 2000);
        });
    } else {
        const textArea = document.createElement("textarea");
        textArea.value = txt;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
        btn.innerText = "COPIED!";
        setTimeout(() => btn.innerText = originalText, 2000);
    }
}