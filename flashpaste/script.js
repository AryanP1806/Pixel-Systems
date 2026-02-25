// --- GLOBAL STATE & CONFIG ---
let snippetCount = 0;
const themeToggle = document.getElementById('themeToggle');

// Initialize with one snippet
window.onload = () => addSnippetInput();

// --- THEME SWITCHER ---
themeToggle.onclick = () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-bs-theme');
    html.setAttribute('data-bs-theme', current === 'dark' ? 'light' : 'dark');
};

// --- SNIPPET MANAGEMENT ---
function addSnippetInput(initialValue = '') {
    snippetCount++;
    const container = document.getElementById('snippet-container');
    const div = document.createElement('div');
    div.className = "mb-3 p-3 bg-body-tertiary border rounded position-relative animate-fade-in";
    div.innerHTML = `
        <div class="d-flex justify-content-between mb-2">
            <label class="x-small fw-bold text-uppercase text-muted">Snippet #${snippetCount}</label>
            <button class="btn-close x-small" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
        <textarea class="form-control snippet-input mb-2" rows="4">${initialValue}</textarea>
        <select class="form-select form-select-sm language-select">
            <option value="text">Plain Text</option>
            <option value="javascript">JavaScript / Code</option>
            <option value="markdown">Markdown</option>
        </select>
    `;
    container.appendChild(div);
}

// --- FILE DROP LOGIC ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');

dropZone.onclick = () => fileInput.click();
dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('bg-primary-subtle'); };
dropZone.ondragleave = () => dropZone.classList.remove('bg-primary-subtle');
dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove('bg-primary-subtle');
    handleFiles(e.dataTransfer.files);
};

fileInput.onchange = (e) => handleFiles(e.target.files);

function handleFiles(files) {
    Array.from(files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => addSnippetInput(e.target.result);
        reader.readAsText(file);
    });
}

// --- E2EE CRYPTO LOGIC ---
async function deriveKey(passcode) {
    const encoder = new TextEncoder();
    const salt = encoder.encode('flashpaste-salt-v2');
    const baseKey = await crypto.subtle.importKey('raw', encoder.encode(passcode), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
        baseKey, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
    );
}

async function encryptData(text, code) {
    const key = await deriveKey(code);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(text);
    const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv); combined.set(new Uint8Array(ciphertext), iv.length);
    return btoa(String.fromCharCode(...combined));
}

async function decryptData(base64, code) {
    try {
        const key = await deriveKey(code);
        const combined = new Uint8Array(atob(base64).split("").map(c => c.charCodeAt(0)));
        const iv = combined.slice(0, 12);
        const ciphertext = combined.slice(12);
        const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ciphertext);
        return new TextDecoder().decode(decrypted);
    } catch(e) { return null; }
}

// --- SEND ACTION ---
document.getElementById('generateBtn').onclick = async () => {
    const inputs = document.querySelectorAll('.snippet-input');
    const langs = document.querySelectorAll('.language-select');
    const useEncryption = document.getElementById('e2eeToggle').checked;
    
    let snippets = [];
    inputs.forEach((input, i) => { if(input.value) snippets.push({ text: input.value, lang: langs[i].value }); });

    if(!snippets.length) return alert("Please add some content.");

    const code = Math.floor(1000 + Math.random() * 9000).toString();
    let payload = JSON.stringify(snippets);

    if(useEncryption) payload = await encryptData(payload, code);

    const fd = new FormData();
    fd.append('content', payload);
    fd.append('code', code);
    if(useEncryption) fd.append('encrypted', 'true');

    const res = await fetch('api.php?action=save', { method: 'POST', body: fd });
    const data = await res.json();

    if(data.success) {
        document.getElementById('finalCode').innerText = data.code;
        document.getElementById('codeResult').classList.remove('d-none');
    }
};

// --- FETCH & URL DETECTION ---
document.getElementById('fetchBtn').onclick = async () => {
    const code = document.getElementById('accessCode').value;
    const res = await fetch(`api.php?action=fetch&code=${code}`);
    const data = await res.json();

    if(!data.success) return alert(data.message);

    let raw = data.content;
    if(data.is_encrypted) {
        raw = await decryptData(raw, code);
        if(!raw) return alert("Decryption failed.");
    }

    renderSnippets(JSON.parse(raw));
};

function renderSnippets(list) {
    const container = document.getElementById('fetched-snippets');
    container.innerHTML = '';
    document.getElementById('displayArea').classList.remove('d-none');
    document.getElementById('welcomeMessage').classList.add('d-none');

    list.forEach(s => {
        const div = document.createElement('div');
        div.className = "mb-4 border-bottom pb-3";
        
        // URL DETECTION logic
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const hasUrl = s.text.match(urlRegex);
        let urlBtn = '';
        if(hasUrl) {
            urlBtn = `<a href="${hasUrl[0]}" target="_blank" class="btn btn-sm btn-info mt-2 text-white">🔗 Open Link</a>`;
        }

        let contentHtml = s.lang === 'markdown' 
            ? `<div class="p-3 bg-body border rounded">${marked.parse(s.text)}</div>` 
            : `<pre class="rounded"><code>${s.text.replace(/</g, "&lt;")}</code></pre>`;

        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="badge bg-secondary text-uppercase">${s.lang}</span>
                <button class="btn btn-link btn-sm p-0 text-decoration-none" onclick="copyRaw('${btoa(s.text)}')">📋 Copy</button>
            </div>
            ${contentHtml}
            ${urlBtn}
        `;
        container.appendChild(div);
    });
    Prism.highlightAll();
}

function copyRaw(b64) {
    navigator.clipboard.writeText(atob(b64));
    alert("Copied!");
}