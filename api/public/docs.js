(() => {
	const specUrl = "/openapi.json";

	function escapeHtml(value) {
		return String(value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;");
	}

	function buildTryLink(path, operation) {
		const params = new URLSearchParams();
		params.set("endpoint", path);
		for (const param of operation.parameters || []) {
			if (param.in === "path" && param.example !== undefined) {
				params.set(param.name, String(param.example));
			}
		}
		return `/playground.html?${params.toString()}`;
	}

	function renderParams(operation) {
		const params = (operation.parameters || []).filter(p => p.in === "path" || p.in === "query");
		if (params.length === 0) return "";

		const rows = params.map(p => `
			<tr>
				<td><code>${escapeHtml(p.name)}</code>${p.required ? ' <span class="required">required</span>' : ""}</td>
				<td><span class="method-loc">${p.in}</span></td>
				<td>${escapeHtml(p.description || "")}</td>
			</tr>`).join("");

		return `
			<table class="param-table">
				<thead><tr><th>Parameter</th><th>In</th><th>Description</th></tr></thead>
				<tbody>${rows}</tbody>
			</table>`;
	}

	function renderEndpoint(path, operation) {
		const methodLabel = "GET";

		return `
			<div class="endpoint">
				<div class="endpoint-head">
					<span class="method get">${methodLabel}</span>
					<code class="endpoint-path">${escapeHtml(path)}</code>
				</div>
				<h4 class="endpoint-summary">${escapeHtml(operation.summary || "")}</h4>
				<p class="endpoint-description">${escapeHtml(operation.description || "")}</p>
				${renderParams(operation)}
				<a class="link" href="${buildTryLink(path, operation)}">Try it in the playground →</a>
			</div>`;
	}

	function renderTag(tagName, paths) {
		const sections = paths
			.map(([path, methods]) => {
				const operation = methods.get;
				return operation ? renderEndpoint(path, operation) : "";
			})
			.join("");

		return `
			<section class="doc-section" id="${tagName}">
				<h2>${tagName === "versions" ? "Versions" : tagName.charAt(0).toUpperCase() + tagName.slice(1)}</h2>
				${sections}
			</section>`;
	}

	function populateReference(spec) {
		const container = document.getElementById("api-reference");
		const groups = {};

		for (const [path, methods] of Object.entries(spec.paths || {})) {
			const operation = methods.get;
			if (!operation) continue;
			const tag = (operation.tags && operation.tags[0]) || "misc";
			(groups[tag] ||= []).push([path, methods]);
		}

		container.innerHTML = Object.entries(groups)
			.map(([tag, paths]) => renderTag(tag, paths))
			.join("");
	}

	// ---------- scroll spy ----------
	const links = Array.from(document.querySelectorAll("#docs-nav-list a"));
	const sections = links
		.map(link => document.getElementById(link.getAttribute("href").slice(1)))
		.filter(Boolean);

	const setActive = id => {
		links.forEach(link =>
			link.classList.toggle("active", link.getAttribute("href") === "#" + id),
		);
	};

	const onScroll = () => {
		let current = sections[0] ? sections[0].id : "";
		const marker = window.scrollY + window.innerHeight / 3;
		for (const section of sections) {
			if (section.getBoundingClientRect().top + window.scrollY <= marker) {
				current = section.id;
			} else {
				break;
			}
		}
		setActive(current);
	};

	window.addEventListener("scroll", onScroll, { passive: true });
	window.addEventListener("resize", onScroll);

	fetch(specUrl)
		.then(res => {
			if (!res.ok) throw new Error(`Failed to load ${specUrl}: HTTP ${res.status}`);
			return res.json();
		})
		.then(populateReference)
		.catch(err => {
			const container = document.getElementById("api-reference");
			container.innerHTML = `<div class="doc-note">Could not load the API reference (${escapeHtml(err.message)}). The spec is available at <a href="/openapi.json">/openapi.json</a>.</div>`;
		})
		.finally(onScroll);
})();
