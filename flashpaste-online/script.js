/**
 * FlashPaste Pro - Frontend Redesign
 * Focus: Binary preservation and 4-digit logic
 */

let snippetCount = 0;

window.onload = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code) {
        document.getElementById('accessCode').value = code;
        document.getElementById('fetchBtn').click();
    }
};

// Theme Toggle
document.getElementById('themeToggle').onclick = () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-bs-theme');
    html.setAttribute('data-bs-theme', current === 'dark' ? 'light' : 'dark');
};

// Helpers for Binary/Base64
function uint8ToBase64(u8Arr) {
    let CHUNK_SIZE = 0x8000;
    let index = 0;
    let result = '';
    while (index < u8Arr.length) {
        let slice = u8Arr.subarray(index, index + CHUNK_SIZE);
        result += String.fromCharCode.apply(null, slice);
        index += CHUNK_SIZE;
    }
    return btoa(result);
}

function base64ToUint8(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

// Snippet Logic
function addSnippetInput(initialValue = '', fileName = '', fileType = 'text') {
    snippetCount++;
    const container = document.getElementById('snippet-container');
    const div = document.createElement('div');
    div.className = "mb-3 p-3 bg-body-tertiary border rounded position-relative animate-fade-in";
    
    const isFile = fileType === 'file';
    div.innerHTML = `
        <div class="d-flex justify-content-between mb-2">
            <label class="x-small fw-bold text-uppercase text-muted">
                ${isFile ? '📎 File Attachment' : '📄 Text Snippet #' + snippetCount} 
            </label>
            <button class="btn-close x-small" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
        ${isFile ? `
            <div class="p-3 border rounded bg-body text-center">
                <div class="mb-1 fw-bold">${fileName}</div>
                <div class="x-small text-success">Ready for transfer</div>
                <input type="hidden" class="snippet-input" data-filename="${fileName}" data-type="file" value="${initialValue}">
            </div>
        ` : `
            <textarea class="form-control snippet-input mb-2" rows="4" data-type="text">${initialValue}</textarea>
            <select class="form-select form-select-sm language-select">
                <option value="text">Plain Text</option>
                <option value="javascript">Code / JavaScript</option>
                <option value="markdown">Markdown</option>
            </select>
        `}
    `;
    container.appendChild(div);
}

// File Input Handling
const fileInput = document.getElementById('fileInput');
document.getElementById('drop-zone').onclick = () => fileInput.click();
fileInput.onchange = (e) => handleFiles(e.target.files);

async function handleFiles(files) {
    for (const file of files) {
        const reader = new FileReader();
        reader.onload = (e) => {
            // ALWAYS treat as binary for transfer integrity
            const base64Data = e.target.result.split(',')[1];
            addSnippetInput(base64Data, file.name, 'file');
        };
        reader.readAsDataURL(file);
    }
}

// Crypto Logic
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
    const encoded = new TextEncoder().encode(text);
    const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(ciphertext), iv.length);
    return uint8ToBase64(combined);
}

async function decryptData(base64, code) {
    try {
        const key = await deriveKey(code);
        const combined = base64ToUint8(base64);
        const iv = combined.slice(0,12);
        const ciphertext = combined.slice(12);
        const decrypted = await crypto.subtle.decrypt({ name:'AES-GCM', iv }, key, ciphertext);
        return new TextDecoder().decode(decrypted);
    } catch(e) { return null; }
}

// ACTION: SEND
document.getElementById('generateBtn').onclick = async () => {
    const inputs = document.querySelectorAll('.snippet-input');
    const langs = document.querySelectorAll('.language-select');
    const useEncryption = document.getElementById('e2eeToggle').checked;
    
    let snippets = [];
    inputs.forEach((input, i) => {
        if(input.value){
            const isFile = input.getAttribute('data-type') === 'file';
            snippets.push({
                content: input.value,
                name: input.getAttribute('data-filename') || 'snippet.txt',
                type: isFile ? 'file' : 'text',
                lang: isFile ? 'binary' : (langs[i]?.value || 'text')
            });
        }
    });

    if(!snippets.length) return alert("Nothing to send.");

    const code = Math.floor(1000 + Math.random() * 9000).toString();
    let payload = JSON.stringify(snippets);

    if(useEncryption) payload = await encryptData(payload, code);

    const fd = new FormData();
    fd.append('content', payload);
    fd.append('code', code);
    fd.append('encrypted', useEncryption ? 'true' : 'false');

    const btn = document.getElementById('generateBtn');
    btn.disabled = true; btn.innerText = "UPLOADING...";

    try {
        const res = await fetch('api.php?action=save', { method: 'POST', body: fd });
        const data = await res.json();
        if(data.success) {
            document.getElementById('finalCode').innerText = data.code;
            document.getElementById('codeResult').classList.remove('d-none');
            btn.innerText = "DONE!";
        } else {
            alert(data.message);
            btn.disabled = false; btn.innerText = "GENERATE CODE";
        }
    } catch(e) {
        alert("Server Error. Check console/logs.");
        btn.disabled = false;
    }
};

// ACTION: FETCH (THE FIX)
document.getElementById('fetchBtn').onclick = async () => {
    const code = document.getElementById('accessCode').value.trim();
    if(code.length !== 4) return alert("Enter the 4-digit code.");

    const btn = document.getElementById('fetchBtn');
    btn.disabled = true; btn.innerText = "...";

    try {
        const res = await fetch(`api.php?action=fetch&code=${code}`);
        const data = await res.json();

        if(!data.success) {
            alert(data.message);
            btn.disabled = false; btn.innerText = "FETCH";
            return;
        }

        let rawPayload = data.content;
        if(data.encrypted) {
            rawPayload = await decryptData(rawPayload, code);
            if(!rawPayload) {
                alert("Decryption failed. Wrong code or corrupted data.");
                btn.disabled = false; btn.innerText = "FETCH";
                return;
            }
        }

        const snippets = JSON.parse(rawPayload);
        displaySnippets(snippets);
        
        document.getElementById('displayArea').classList.remove('d-none');
        document.getElementById('welcomeMessage').classList.add('d-none');
        btn.disabled = false; btn.innerText = "FETCH";

    } catch(e) {
        alert("Transfer Error.");
        btn.disabled = false; btn.innerText = "FETCH";
    }
};

function displaySnippets(snippets) {
    const container = document.getElementById('fetched-snippets');
    container.innerHTML = '';
    
    snippets.forEach(s => {
        const div = document.createElement('div');
        div.className = "mb-4 p-3 border rounded bg-body shadow-sm animate-fade-in";
        
        if(s.type === 'file') {
            div.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div><span class="opacity-50">File:</span> <strong>${s.name}</strong></div>
                    <button class="btn btn-primary btn-sm" onclick="downloadFile('${s.content}', '${s.name}')">Download Now</button>
                </div>
            `;
        } else {
            div.innerHTML = `
                <div class="small text-muted mb-2 text-uppercase fw-bold">${s.lang}</div>
                <pre class="rounded mb-2"><code>${s.content}</code></pre>
                <button class="btn btn-sm btn-outline-dark" onclick="copySnippet(this, \`${s.content.replace(/`/g, '\\`')}\`)">Copy Text</button>
            `;
        }
        container.appendChild(div);
    });
    if(window.Prism) Prism.highlightAll();
}

function downloadFile(base64, name) {
    const link = document.createElement('a');
    link.href = `data:application/octet-stream;base64,${base64}`;
    link.download = name;
    link.click();
}

function copySnippet(btn, text) {
    navigator.clipboard.writeText(text);
    btn.innerText = "Copied!";
    setTimeout(() => btn.innerText = "Copy Text", 2000);
}