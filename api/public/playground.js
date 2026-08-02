(() => {
    const specUrl = "/openapi.json";

    const listEl = document.getElementById("pg-list");
    const paramsEl = document.getElementById("pg-params");
    const urlEl = document.getElementById("pg-url");
    const sendBtn = document.getElementById("pg-send");
    const statusEl = document.getElementById("pg-status");
    const latencyEl = document.getElementById("pg-latency");
    const sizeEl = document.getElementById("pg-size");
    const bodyEl = document.getElementById("pg-body");
    const copyBtn = document.getElementById("pg-copy");
    const toggleEl = document.getElementById("pg-snippet-toggle");
    const curlCodeEl = document.getElementById("pg-code-curl");
    const fetchCodeEl = document.getElementById("pg-code-fetch");
    const curlBox = document.getElementById("pg-snippet-curl");
    const fetchBox = document.getElementById("pg-snippet-fetch");
    const subtitleEl = document.getElementById("pg-subtitle");

    const entries = [];
    let activePath = null;

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function getOperation() {
        return entries.find(e => e.path === activePath)?.operation || null;
    }

    function readParams() {
        const values = {};
        document.querySelectorAll("[data-param]").forEach(inp => {
            values[inp.dataset.param] = inp.value.trim();
        });
        return values;
    }

    function buildUrl() {
        if (!activePath) return "";
        const values = readParams();
        let path = activePath;

        for (const match of path.matchAll(/\{([^}]+)\}/g)) {
            const name = match[1];
            path = path.replace(`{${name}}`, encodeURIComponent(values[name] || ""));
        }

        const queries = (getOperation()?.parameters || []).filter(p => p.in === "query");
        const qs = new URLSearchParams();
        for (const q of queries) {
            const value = values[q.name];
            if (value) qs.set(q.name, value);
        }

        const qsString = qs.toString();
        return qsString ? `${path}?${qsString}` : path;
    }

    function renderUrl() {
        urlEl.innerHTML = `<span class="method get">GET</span> <span class="pg-url-path">${escapeHtml(buildUrl())}</span>`;
    }

    function renderParams() {
        paramsEl.innerHTML = "";
        const operation = getOperation();
        if (!operation) return;

        for (const p of operation.parameters || []) {
            if (p.in !== "path" && p.in !== "query") continue;
            const row = document.createElement("div");
            row.className = "pg-param-row";
            row.innerHTML = `
                <label class="pg-param-label">
                    <span>${escapeHtml(p.name)}${p.required ? ' <span class="required">required</span>' : ""}</span>
                    <span class="pg-param-loc">${escapeHtml(p.in)}</span>
                </label>
                <input type="text" data-param="${escapeHtml(p.name)}"
                    placeholder="${escapeHtml(p.description || p.name)}" spellcheck="false">`;
            paramsEl.appendChild(row);
        }
    }

    function renderSnippets() {
        const url = buildUrl();
        curlCodeEl.textContent = `curl "${url}"`;
        fetchCodeEl.textContent =
            `fetch("${url}")\n  .then(res => res.json())\n  .then(data => console.log(data));`;
    }

    function renderList() {
        const groups = {};
        for (const entry of entries) {
            (groups[entry.tag] ||= []).push(entry);
        }

        listEl.innerHTML = "";
        for (const [tag, group] of Object.entries(groups)) {
            const label = document.createElement("div");
            label.className = "pg-group";
            label.textContent = tag;
            listEl.appendChild(label);

            for (const entry of group) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "pg-item";
                button.dataset.path = entry.path;
                button.innerHTML =
                    `<span class="method get">GET</span><span class="pg-item-path">${escapeHtml(entry.path)}</span>`;
                button.addEventListener("click", () => selectEndpoint(entry.path));
                listEl.appendChild(button);
            }
        }
    }

    function selectEndpoint(path, prefill = {}) {
        activePath = path;
        renderParams();

        for (const [name, value] of Object.entries(prefill)) {
            const input = document.querySelector(`[data-param="${CSS.escape(name)}"]`);
            if (input) input.value = value;
        }

        renderUrl();
        renderSnippets();
        document.querySelectorAll(".pg-item").forEach(button =>
            button.classList.toggle("active", button.dataset.path === path),
        );
    }

    async function send() {
        const url = buildUrl();
        if (!url) return;

        sendBtn.disabled = true;
        statusEl.textContent = "…";
        statusEl.className = "status-badge";
        latencyEl.textContent = "";
        sizeEl.textContent = "";

        const start = performance.now();
        try {
            const response = await fetch(url);
            const elapsed = Math.round(performance.now() - start);
            const text = await response.text();

            statusEl.textContent = `${response.status} ${response.statusText}`;
            statusEl.className = `status-badge ${response.ok ? "ok" : "err"}`;
            latencyEl.textContent = `${elapsed} ms`;
            sizeEl.textContent = `${new Blob([text]).size.toLocaleString()} bytes`;

            try {
                bodyEl.textContent = JSON.stringify(JSON.parse(text), null, 2);
            } catch {
                bodyEl.textContent = text || "(empty body)";
            }
        } catch (err) {
            statusEl.textContent = "ERROR";
            statusEl.className = "status-badge err";
            latencyEl.textContent = "";
            sizeEl.textContent = "";
            bodyEl.textContent = String(err.message || err);
        } finally {
            sendBtn.disabled = false;
        }
    }

    toggleEl.addEventListener("click", event => {
        const button = event.target.closest("button");
        if (!button) return;
        toggleEl.querySelectorAll("button").forEach(b =>
            b.classList.toggle("active", b === button),
        );
        curlBox.classList.toggle("visible", button.dataset.kind === "curl");
        fetchBox.classList.toggle("visible", button.dataset.kind === "fetch");
    });

    copyBtn.addEventListener("click", () => {
        const kind = toggleEl.querySelector("button.active")?.dataset.kind;
        const text = kind === "fetch" ? fetchCodeEl.textContent : curlCodeEl.textContent;
        navigator.clipboard?.writeText(text).then(() => {
            copyBtn.textContent = "Copied!";
            setTimeout(() => (copyBtn.textContent = "Copy code"), 1500);
        });
    });

    sendBtn.addEventListener("click", send);

    fetch(specUrl)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(spec => {
            for (const [path, methods] of Object.entries(spec.paths || {})) {
                const operation = methods.get;
                if (!operation) continue;
                entries.push({
                    tag: (operation.tags && operation.tags[0]) || "misc",
                    path,
                    operation,
                });
            }
            entries.sort((a, b) => a.path.localeCompare(b.path));

            renderList();
            subtitleEl.textContent =
                `Live against the latest build · ${Object.keys(spec.paths).length} endpoints`;

            const query = new URLSearchParams(location.search);
            const target = query.get("endpoint");
            const prefill = {};
            query.forEach((value, key) => {
                if (key !== "endpoint") prefill[key] = value;
            });

            if (target && entries.some(e => e.path === target)) {
                selectEndpoint(target, prefill);
            } else if (entries.length) {
                selectEndpoint(entries[0].path);
            }
        })
        .catch(err => {
            subtitleEl.textContent = `Could not load the API spec: ${err.message}`;
            listEl.innerHTML = `<div class="pg-empty" style="padding:14px">OpenAPI spec unavailable.</div>`;
        });
})();
