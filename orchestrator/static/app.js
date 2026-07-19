import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.14.1/+esm";

const select = (selector) => document.querySelector(selector);
let currentCallId = null;
let activeConversation = null;
let callEndTimer = null;
let farewellPending = false;
let resultSaved = false;
let animatedOfferId = null;
let lastRenderedCallId = null;
let campaignStartedThisPage = false;

function clearCallEndTimer() {
	if (callEndTimer !== null) window.clearTimeout(callEndTimer);
	callEndTimer = null;
}

function endConversationSoon(conversation, delay = 1200) {
	clearCallEndTimer();
	callEndTimer = window.setTimeout(() => {
		void conversation?.endSession();
	}, delay);
}

function enforceCallLimit(conversation) {
	clearCallEndTimer();
	farewellPending = false;
	resultSaved = false;
	callEndTimer = window.setTimeout(() => {
		select("#voice-status").textContent = "Call time limit reached; ending…";
		void conversation?.endSession();
	}, 180000);
}

function messageText(message) {
	if (typeof message === "string") return message;
	if (!message || typeof message !== "object") return "";
	return (
		message.message ||
		message.agent_response ||
		message.agent_response_event?.agent_response ||
		message.text ||
		""
	);
}

function isFarewell(message) {
	return /\b(goodbye|bye-bye|have a great day|end the call now)\b/i.test(messageText(message));
}

function animateIncomingAnswer(call, isNextCarrier) {
	if (
		!isNextCarrier ||
		call.status !== "offered_to_widget" ||
		animatedOfferId === call.id
	)
		return;
	const answer = select("#answer");
	animatedOfferId = call.id;
	answer.classList.remove("incoming-answer");
	void answer.offsetWidth;
	answer.classList.add("incoming-answer");
	answer.scrollIntoView({ behavior: "smooth", block: "center" });
	answer.focus({ preventScroll: true });
}

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

function jsonArray(value) {
	if (Array.isArray(value)) return value;
	if (typeof value !== "string" || !value.trim()) return [];
	try {
		const parsed = JSON.parse(value);
		return Array.isArray(parsed) ? parsed : [];
	} catch {
		return [];
	}
}

function structuredResult(params) {
	return {
		outcome: params.outcome,
		initial_total: params.initial_total ?? null,
		final_total: params.final_total ?? null,
		fees: jsonArray(params.fees_json),
		included_services: jsonArray(params.included_services_json),
		excluded_services: jsonArray(params.excluded_services_json),
		binding: params.binding || "unknown",
		availability: params.availability || "",
		deposit_terms: params.deposit_terms || "",
		cancellation_terms: params.cancellation_terms || "",
		quote_validity: params.quote_validity || "",
		notes: params.notes || "",
	};
}

async function reconcileUntilSettled(callId, attempts = 8) {
	for (let attempt = 0; attempt < attempts; attempt += 1) {
		try {
			const result = await api(`/api/calls/${callId}/reconcile`, {
				method: "POST",
			});
			if (result.reconciled || ["done", "failed"].includes(result.status)) break;
		} catch {
			// The client tool is primary; reconciliation is a best-effort backstop.
		}
		await new Promise((resolve) => setTimeout(resolve, 2000));
	}
	try {
		render(await api("/api/state"));
	} catch {
		// SSE will retry state delivery if this immediate refresh fails.
	}
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
		campaignStartedThisPage = true;
		document.body.classList.add("campaign-started");
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
				`<div class="job"><span class="number">${job.sequence_no}</span><div><strong>${job.carrier.carrier_name}</strong><br><small>${job.carrier.location} · USDOT ${job.carrier.dot_number} · ${job.carrier.headline}</small></div><span class="badge ${job.status}">${job.status.replaceAll("_", " ")}</span></div>`,
		)
		.join("");
	const offered = campaign.jobs.find(
		(job) => job.status === "offered_to_widget",
	);
	const claimed = campaign.jobs.find((job) => job.status === "claimed");
	const active = campaign.jobs.find((job) => job.status === "in_progress");
	const call = offered || claimed || active;
	if (call) {
		const isNextCarrier =
			campaignStartedThisPage &&
			lastRenderedCallId !== null &&
			lastRenderedCallId !== call.id;
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
		animateIncomingAnswer(call, isNextCarrier);
		lastRenderedCallId = call.id;
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
	renderCallResults(campaign);
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

function renderCallResults(campaign) {
	const container = select("#call-results");
	container.replaceChildren();
	const completed = campaign.jobs.filter((job) => job.result);
	if (completed.length === 0) return;
	const title = document.createElement("h3");
	title.textContent = "Structured call records";
	container.append(title);
	for (const job of completed) {
		const result = job.result;
		const record = document.createElement("article");
		record.className = "persona";
		const heading = document.createElement("strong");
		heading.textContent = `${job.carrier.carrier_name} · ${result.outcome}`;
		const details = document.createElement("pre");
		details.textContent = JSON.stringify(
			{
				initial_total: result.initial_total,
				final_total: result.final_total,
				fees: result.fees,
				included_services: result.included_services,
				excluded_services: result.excluded_services,
				binding: result.binding,
				availability: result.availability,
				deposit_terms: result.deposit_terms,
				cancellation_terms: result.cancellation_terms,
				quote_validity: result.quote_validity,
				notes: result.notes,
			},
			null,
			2,
		);
		record.append(heading, details);
		container.append(record);
	}
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
			clientTools: {
				save_quote_progress: async (params) =>
					api(`/api/calls/${callId}/progress`, {
						method: "POST",
						body: JSON.stringify({
							initial_total: params.initial_total ?? null,
							fees: jsonArray(params.fees_json),
							notes: params.notes || "",
						}),
					}),
				save_negotiation_result: async (params) => {
					const saved = await api(`/api/calls/${callId}/result`, {
						method: "POST",
						body: JSON.stringify(structuredResult(params)),
					});
					resultSaved = true;
					return saved;
				},
			},
			onConnect: () => {
				select("#voice-status").textContent = "Connected to The Negotiator";
				select("#hang-up").classList.remove("hidden");
			},
			onMessage: (message) => {
				if (!resultSaved && isFarewell(message)) {
					farewellPending = true;
					endConversationSoon(activeConversation || pendingConversation, 15000);
				}
			},
			onModeChange: (mode) => {
				const modeName = typeof mode === "string" ? mode : mode?.mode;
				if (farewellPending && modeName === "listening") {
					endConversationSoon(activeConversation || pendingConversation, 250);
				}
			},
			onDisconnect: () => {
				select("#voice-status").textContent = "Call ended";
				select("#hang-up").classList.add("hidden");
				voiceSession.classList.add("hidden");
				answer.disabled = false;
				answer.textContent = "Answer";
				activeConversation = null;
				clearCallEndTimer();
				farewellPending = false;
				resultSaved = false;
				void reconcileUntilSettled(callId);
			},
			onError: (error) => {
				select("#form-error").textContent = `Voice call error: ${error.message || error}`;
			},
		});
		activeConversation = pendingConversation;
		enforceCallLimit(pendingConversation);
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
		clearCallEndTimer();
		farewellPending = false;
		resultSaved = false;
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
