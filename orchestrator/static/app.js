import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.14.1/+esm";

const select = (selector) => document.querySelector(selector);
let currentCallId = null;
let activeConversation = null;

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
	const claimed = campaign.jobs.find((job) => job.status === "claimed");
	const active = campaign.jobs.find((job) => job.status === "in_progress");
	const call = offered || claimed || active;
	if (call) {
		currentCallId = call.id;
		select("#call-card").classList.remove("hidden");
		select("#caller-name").textContent = "Incoming call from The Negotiator";
		select("#caller-style").textContent =
			"AI assistant calling on behalf of a customer";
		select("#answering-as").textContent =
			`You are answering as ${call.carrier.carrier_name} · ${call.carrier.headline}`;
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
	const answer = select("#answer");
	const voiceSession = select("#voice-session");
	const callId = currentCallId;
	let claimToken = null;
	let pendingConversation = null;
	answer.disabled = true;
	answer.textContent = "Answering…";
	select("#form-error").textContent = "";
	voiceSession.classList.remove("hidden");
	select("#voice-status").textContent = "Requesting microphone access…";

	try {
		const permissionStream = await navigator.mediaDevices.getUserMedia({
			audio: true,
		});
		permissionStream.getTracks().forEach((track) => track.stop());
		const session = await api(`/api/calls/${callId}/answer`, { method: "POST" });
		claimToken = session.claim_token;
		select("#voice-status").textContent = "Connecting…";
		pendingConversation = await Conversation.startSession({
			signedUrl: session.signed_url,
			dynamicVariables: session.dynamic_variables,
			onConnect: () => {
				select("#voice-status").textContent = "Connected to The Negotiator";
				select("#hang-up").classList.remove("hidden");
			},
			onDisconnect: () => {
				select("#voice-status").textContent = "Call ended";
				select("#hang-up").classList.add("hidden");
				activeConversation = null;
			},
			onError: (error) => {
				select("#form-error").textContent = `Voice call error: ${error.message || error}`;
			},
		});
		activeConversation = pendingConversation;
		await api(`/api/calls/${callId}/started`, {
			method: "POST",
			body: JSON.stringify({
				claim_token: claimToken,
				conversation_id: pendingConversation.getId(),
			}),
		});
		claimToken = null;
	} catch (error) {
		if (pendingConversation) {
			try {
				await pendingConversation.endSession();
			} catch {
				// The failed SDK session may already be disconnected.
			}
		}
		activeConversation = null;
		if (claimToken) {
			try {
				await api(`/api/calls/${callId}/release`, {
					method: "POST",
					body: JSON.stringify({ claim_token: claimToken }),
				});
			} catch {
				// A concurrent successful start owns the claim and must not be rolled back.
			}
		}
		voiceSession.classList.add("hidden");
		answer.disabled = false;
		answer.textContent = "Answer";
		select("#form-error").textContent = `Could not answer call: ${error.message || error}`;
	}
});

select("#hang-up").addEventListener("click", async () => {
	if (activeConversation) await activeConversation.endSession();
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
	if (activeConversation) await activeConversation.endSession();
	select("#voice-session").classList.add("hidden");
});

api("/api/state").then(render);
