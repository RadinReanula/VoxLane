# Customer and operator experience

## Customer lane display

The lane display is a glanceable companion to speech, not a touchscreen menu.
It presents one dominant system state, live captions, a persistent order card,
the total, and concise recovery instructions.

States:

- `approaching`: attract screen before the simulated sensor fires
- `greeting`: short welcome while the session starts
- `listening`: stable cyan ring and “I’m listening”
- `processing`: restrained pulse and the accepted transcript
- `speaking`: response caption and speaker indicator
- `confirming`: complete itemized summary and explicit confirmation prompt
- `complete`: order number and handoff instruction
- `recovering`: retry status with no blame assigned to the customer
- `human_help`: clear operator takeover message

Partial transcripts are visually distinct from final transcripts. Cart changes
animate only after deterministic order events are received; the UI never
optimistically invents an order update from raw transcript text.

## Operator console

The console is for development, demos, and escalation. It provides simulated
vehicle controls, session state, current/final transcripts, provider mode,
timing spans, order events, failures, disconnect, and human takeover. Customer
content is hidden from ordinary operational logs unless diagnostic retention is
explicitly enabled.

## Visual system

- Midnight `#07111F`: page background
- Raised `#101C2C`: cards and panels
- Text `#F8FAFC`: primary copy
- Muted `#CBD5E1`: secondary copy
- Cyan `#22D3EE`: active/listening
- Green `#4ADE80`: confirmed/success
- Amber `#FBBF24`: waiting/warning
- Rose `#FB7185`: error/escalation

Color is always paired with an icon and text. Normal text must meet 4.5:1
contrast; large text and controls must meet at least 3:1. Customer typography
starts at 24 px, with the primary state substantially larger for outdoor
readability.

Motion uses opacity and transform only, avoids fake progress, and stops on state
transition. `prefers-reduced-motion` replaces pulses and waves with static
indicators. Status and captions use appropriate `aria-live` regions. Operator
controls are keyboard accessible and have visible focus.

## Responsive targets

- 1920×1080 and 1366×768 landscape kiosk
- ordinary laptop browser for the zero-budget demo
- narrow tablet as a diagnostic convenience, not a driving interaction target
