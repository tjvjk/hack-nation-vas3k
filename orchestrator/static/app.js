import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.14.1/+esm";

const select = (selector) => document.querySelector(selector);
let currentCallId = null;
let activeConversation = null;
let callEndTimer = null;
let callDurationTimer = null;
let callStartedAt = null;
let farewellPending = false;
let resultSaved = false;
let animatedOfferId = null;
let lastRenderedCallId = null;
let campaignStartedThisPage = false;

function clearCallEndTimer() {
	if (callEndTimer !== null) window.clearTimeout(callEndTimer);
	callEndTimer = null;
}

function formatCallDuration(totalSeconds) {
	const minutes = Math.floor(totalSeconds / 60);
	const seconds = totalSeconds % 60;
	return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function updateCallDuration() {
	const elapsedSeconds = callStartedAt
		? Math.floor((Date.now() - callStartedAt) / 1000)
		: 0;
	select("#call-timer").textContent = formatCallDuration(elapsedSeconds);
}

function startCallDurationTimer() {
	if (callDurationTimer !== null) window.clearInterval(callDurationTimer);
	callStartedAt = Date.now();
	updateCallDuration();
	callDurationTimer = window.setInterval(updateCallDuration, 1000);
}

function stopCallDurationTimer() {
	if (callDurationTimer !== null) window.clearInterval(callDurationTimer);
	callDurationTimer = null;
	callStartedAt = null;
}

function resetCallDurationTimer() {
	stopCallDurationTimer();
	select("#call-timer").textContent = "00:00";
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
		select("#voice-status").textContent = "Call time limit reached; ending...";
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

function clearSubtitles() {
	select("#subtitles-list").innerHTML = '<p class="empty-subtitles">Subtitles will appear after you answer.</p>';
}

function setPostCallProcessing(visible) {
	select("#post-call-processing").classList.toggle("hidden", !visible);
}

function scrollSubtitlesToBottom() {
	const list = select("#subtitles-list");
	requestAnimationFrame(() => {
		list.scrollTop = list.scrollHeight;
	});
}

function appendSubtitle(message) {
	const text = messageText(message).trim();
	if (!text) return;
	const list = select("#subtitles-list");
	list.querySelector(".empty-subtitles")?.remove();
	const row = document.createElement("p");
	const speaker = message?.source === "user" || message?.role === "user" ? "You" : "Agent";
	const label = document.createElement("strong");
	label.textContent = speaker;
	row.append(label, text);
	list.append(row);
	while (list.children.length > 12) list.firstElementChild.remove();
	scrollSubtitlesToBottom();
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

function saturdayThreeWeeksFromNow() {
	const date = new Date(Date.now() + 21 * 86400000);
	date.setDate(date.getDate() + ((6 - date.getDay() + 7) % 7));
	return date.toISOString().slice(0, 10);
}

function requestPayloadFromText(requestText) {
	return {
		origin: "Rock Hill, SC",
		destination: "Charlotte, NC",
		move_date: saturdayThreeWeeksFromNow(),
		budget_min: 1500,
		budget_max: 2800,
		service_type: "truck_and_movers",
		bedrooms: 2,
		movers_count: 2,
		origin_floor: 2,
		destination_floor: 2,
		origin_elevator: false,
		destination_elevator: false,
		long_carry: false,
		parking_constraints: "Standard stairs at both buildings",
		inventory: [
			{ name: "Sofa", quantity: 1, large: true },
			{ name: "Queen bed and mattress", quantity: 1, large: true },
			{ name: "Refrigerator", quantity: 1, large: true },
			{ name: "Washing machine", quantity: 1, large: true },
			{ name: "Dining table for 4", quantity: 1, large: true },
			{ name: "Boxes", quantity: 15, large: false },
		],
		notes: requestText,
		confirmed: true,
		outreach_consent: true,
		max_carriers: 3,
	};
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

select("#move-form").addEventListener("submit", async (event) => {
	event.preventDefault();
	select("#form-error").textContent = "";
	const form = new FormData(event.currentTarget);
	const requestText = String(form.get("request_text") || "").trim();
	if (!requestText) {
		select("#form-error").textContent = "Describe what the agent should handle.";
		return;
	}
	const payload = requestPayloadFromText(requestText);
	try {
		const move = await api("/api/moves", {
			method: "POST",
			body: JSON.stringify(payload),
		});
		const campaign = await api(`/api/moves/${move.id}/campaign`, { method: "POST" });
		campaignStartedThisPage = true;
		document.body.classList.add("campaign-started");
		render({ campaigns: [campaign] });
		select("#call-card").scrollIntoView({ behavior: "smooth", block: "center" });
		select("#call-card").focus({ preventScroll: true });
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
		select("#call-progress-text").textContent = `Call ${call.sequence_no} of ${campaign.jobs.length} companies`;
		select("#caller-name").textContent = "Calling on your behalf...";
		select("#caller-style").textContent = call.carrier.carrier_name;
		select("#answering-as").textContent =
			`You are answering as ${call.carrier.carrier_name}`;
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
	} else {
		select("#call-card").classList.add("hidden");
	}
	if (campaign.jobs.some((job) => job.result)) renderResults(campaign);
}

function renderResults(campaign) {
	setPostCallProcessing(false);
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
	title.textContent = "Call results";
	container.append(title);
	for (const job of completed) {
		const result = job.result;
		const record = document.createElement("article");
		record.className = "persona result-summary";
		const heading = document.createElement("strong");
		heading.textContent = job.carrier.carrier_name;
		const details = document.createElement("p");
		const lines = [
			`Outcome: ${result.outcome.replaceAll("_", " ")}.`,
			result.final_total != null ? `Final total: $${result.final_total}.` : "",
			result.initial_total != null ? `Initial total: $${result.initial_total}.` : "",
			result.included_services?.length ? `Included: ${result.included_services.join(", ")}.` : "",
			result.excluded_services?.length ? `Excluded: ${result.excluded_services.join(", ")}.` : "",
			result.fees?.length ? `Fees: ${result.fees.map((fee) => fee.name || JSON.stringify(fee)).join(", ")}.` : "",
			result.binding && result.binding !== "unknown" ? `Binding: ${result.binding}.` : "",
			result.availability ? `Availability: ${result.availability}.` : "",
			result.deposit_terms ? `Deposit: ${result.deposit_terms}.` : "",
			result.cancellation_terms ? `Cancellation: ${result.cancellation_terms}.` : "",
			result.quote_validity ? `Quote valid: ${result.quote_validity}.` : "",
			result.notes ? `Notes: ${result.notes}` : "",
		].filter(Boolean);
		details.textContent = lines.join(" ");
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
	clearSubtitles();
	resetCallDurationTimer();
	setPostCallProcessing(false);
	answer.disabled = true;
	answer.textContent = "Answering...";
	select("#form-error").textContent = "";
	voiceSession.classList.remove("hidden");
	select("#voice-status").textContent = "Requesting microphone access...";

	try {
		const permissionStream = await navigator.mediaDevices.getUserMedia({
			audio: true,
		});
		permissionStream.getTracks().forEach((track) => track.stop());
		const session = await api(`/api/calls/${callId}/answer`, { method: "POST" });
		claimToken = session.claim_token;
		select("#voice-status").textContent = "Connecting...";
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
				select("#voice-status").textContent = "Connected to Call Assistant";
				startCallDurationTimer();
				select("#hang-up").classList.remove("hidden");
			},
			onMessage: (message) => {
				appendSubtitle(message);
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
				stopCallDurationTimer();
				setPostCallProcessing(true);
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
		resetCallDurationTimer();
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
