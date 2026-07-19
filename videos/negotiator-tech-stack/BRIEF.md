---
workflow: product-launch-video
flow: automation
storyboard: no
message: "The Negotiator turns a moving quote workflow into an auditable AI negotiation system."
destination: website
aspect: 1920x1080
language: en
audience: hackathon judges and technical product reviewers
length: 45s
angle: technical showcase
narration: no
style_preset: blue-professional
---

## Intent

A concise, diagram-led technical showcase of the currently implemented stack. It
shows the product surface, then traces the real control flow from Docker Compose
through the Python/Starlette MCP service and JavaScript widget to ElevenLabs
Agents, moveBuddha, and Google Maps geocoding. Tone: precise, energetic, and
credible rather than salesy.

## Assets

- Repository source and README — factual source of the stack diagram and product claims.
- http://localhost:8000 — requested browser source; unavailable during capture, so it is represented from the checked-in UI source rather than an invented screenshot.

## Customizations

- Build architectural diagrams for Docker Compose, Python + JavaScript, ElevenLabs Agents API, moveBuddha, and Google Maps API.
- Keep the video text-led and silent: the requested technical explanation is carried by diagrams and animated labels.

## Notes

- Do not expose secrets, keys, or personally identifiable move data.
- The app's browser automation service and local web server were unavailable during capture; claims must remain grounded in repository code and documentation.
