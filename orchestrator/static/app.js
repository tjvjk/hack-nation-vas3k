const select = (selector) => document.querySelector(selector);
let currentCallId = null;

function inventoryFrom(text) {
	return text
		.split("\n")
		.filter(Boolean)
		.map((line) => {
			const [name, quantity = "1", large = "false"] = line
				.split(",")
				.map((part) => part.trim());
			return {
				name,
				quantity: Number(quantity),
				large: large.toLowerCase() === "true",
			};
		});
}

async function api(url, options = {}) {
	const response = await fetch(url, {
		headers: { "Content-Type": "application/json" },
		...options,
	});
	const body = await response.json();
	if (!response.ok) throw new Error(body.error || JSON.stringify(body));
	return body;
}

select("#move-form [name=move_date]").valueAsDate = new Date(
	Date.now() + 14 * 86400000,
);
select("#move-form").addEventListener("submit", async (event) => {
	event.preventDefault();
	select("#form-error").textContent = "";
	const form = new FormData(event.currentTarget);
	const bool = (name) => form.get(name) === "on";
	const payload = {
		origin: form.get("origin"),
		destination: form.get("destination"),
		move_date: form.get("move_date"),
		budget_min: Number(form.get("budget_min")),
		budget_max: Number(form.get("budget_max")),
		service_type: form.get("service_type"),
		bedrooms: Number(form.get("bedrooms")),
		movers_count: Number(form.get("movers_count")),
		origin_floor: Number(form.get("origin_floor")),
		destination_floor: Number(form.get("destination_floor")),
		origin_elevator: bool("origin_elevator"),
		destination_elevator: bool("destination_elevator"),
		long_carry: bool("long_carry"),
		parking_constraints: "",
		inventory: inventoryFrom(form.get("inventory")),
		notes: form.get("notes"),
		confirmed: bool("confirmed"),
		outreach_consent: bool("outreach_consent"),
		max_carriers: 3,
	};
	try {
		const move = await api("/api/moves", {
			method: "POST",
			body: JSON.stringify(payload),
		});
		await api(`/api/moves/${move.id}/campaign`, { method: "POST" });
		select("#intake-card").classList.add("hidden");
		listen();
	} catch (error) {
		select("#form-error").textContent = error.message;
	}
});

function render(state) {
	const campaign = state.campaigns?.[0];
	if (!campaign) return;
	select("#campaign-card").classList.remove("hidden");
	select("#jobs").innerHTML = campaign.jobs
		.map(
			(job) =>
				`<div class="job"><span class="number">${job.sequence_no}</span><div><strong>${job.carrier.carrier_name}</strong><br><small>${job.carrier.headline}</small></div><span class="badge ${job.status}">${job.status.replaceAll("_", " ")}</span></div>`,
		)
		.join("");
	const offered = campaign.jobs.find(
		(job) => job.status === "offered_to_widget",
	);
	const active = campaign.jobs.find((job) => job.status === "in_progress");
	const call = offered || active;
	if (call) {
		currentCallId = call.id;
		select("#call-card").classList.remove("hidden");
		select("#caller-name").textContent = call.carrier.carrier_name;
		select("#caller-style").textContent = call.carrier.headline;
		select("#persona").innerHTML =
			`<strong>Private operator card</strong><p>${call.carrier.private_brief}</p>`;
		select("#answer").classList.toggle(
			"hidden",
			call.status !== "offered_to_widget",
		);
		select("#decline").classList.toggle(
			"hidden",
			call.status !== "offered_to_widget",
		);
		select("#result-form").classList.toggle("hidden", call.status !== "in_progress");
	} else {
		select("#call-card").classList.add("hidden");
	}
	if (campaign.jobs.some((job) => job.result)) renderResults(campaign);
}

function renderResults(campaign) {
	select("#results-card").classList.remove("hidden");
	select("#benchmark").innerHTML =
		`<strong>Benchmark:</strong> $${campaign.benchmark.low}–$${campaign.benchmark.high}`;
	const ranking = campaign.ranking;
	if (ranking.length === 0) {
		select("#ranking").replaceChildren(
			document.createTextNode("No itemized quotes yet."),
		);
		return;
	}
	select("#ranking").innerHTML =
		`<table><thead><tr><th>Carrier</th><th>Final</th><th>Risk</th><th>Verdict</th></tr></thead><tbody>${ranking.map((row) => `<tr class="${row.recommended ? "recommended" : ""}"><td>${row.carrier_name}</td><td>$${row.final_total}</td><td class="flag">${row.red_flags.join(", ") || "—"}</td><td>${row.recommended ? "✓ Recommended" : ""}</td></tr>`).join("")}</tbody></table>`;
}

function listen() {
	const events = new EventSource("/api/events");
	events.addEventListener("state", (event) => {
		try {
			render(JSON.parse(event.data));
		} catch {
			// ignore malformed SSE data
		}
	});
}

select("#answer").addEventListener("click", async () => {
	await api(`/api/calls/${currentCallId}/answer`, { method: "POST" });
	const session = await api(`/api/calls/${currentCallId}/session`);
	const host = select("#voice-widget");
	host.replaceChildren();
	if (session.mode === "live") {
		const widget = document.createElement("elevenlabs-convai");
		widget.setAttribute("signed-url", session.signed_url);
		widget.setAttribute(
			"dynamic-variables",
			JSON.stringify(session.dynamic_variables),
		);
		host.append(widget);
	} else {
		const msg = document.createElement("p");
		msg.textContent =
			"Agent setup unavailable: Agent Negotiator must be created automatically from prompts.py before the server starts. Check the startup log.";
		host.append(msg);
	}
});

select("#decline").addEventListener("click", () =>
	api(`/api/calls/${currentCallId}/decline`, { method: "POST" }),
);
select("#result-form").addEventListener("submit", async (event) => {
	event.preventDefault();
	const form = new FormData(event.currentTarget);
	let fees;
	try {
		fees = JSON.parse(form.get("fees") || "[]");
	} catch {
		select("#form-error").textContent = "Fees must be valid JSON";
		return;
	}
	const number = (name) =>
		form.get(name) === "" ? null : Number(form.get(name));
	await api(`/api/calls/${currentCallId}/result`, {
		method: "POST",
		body: JSON.stringify({
			outcome: form.get("outcome"),
			initial_total: number("initial_total"),
			final_total: number("final_total"),
			fees,
			notes: form.get("result_notes"),
			included_services: [],
			excluded_services: [],
			binding: "unknown",
		}),
	});
	event.currentTarget.reset();
	select("#voice-widget").replaceChildren();
});

api("/api/state").then(render);
