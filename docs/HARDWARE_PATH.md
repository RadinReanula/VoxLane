# Physical pilot path

## Prototype

The software milestone uses a vehicle-arrival button and the laptop microphone
and speaker. This keeps acoustic, conversational, and order-domain validation
independent from hardware purchasing.

## Presence sensor

For an outdoor lane, evaluate an IP-rated FMCW radar that can detect stationary
and moving vehicles while excluding pedestrians. An inductive loop remains the
high-reliability alternative when pavement work is acceptable. The adapter
contract should expose `arrived`, `present`, `departed`, health, signal quality,
and timestamp events; the conversation service should not know the sensor
brand.

Do not treat HC-SR04, a hobby IR beam, or camera-only detection as an
all-weather production solution. They can support sheltered bench experiments.
A camera may later provide secondary analytics after privacy review, but it is
not required to open a voice session.

## Acoustic station

The outdoor pilot needs a directional weather-resistant microphone, a speaker,
an enclosure, controlled mounting geometry, and full-duplex echo testing.
Measure signal-to-noise ratio and echo return loss at multiple vehicle heights
and distances. Browser DSP is sufficient for the laptop milestone, not proof
that the final speaker post is acoustically solved.

## Sensor acceptance tests

- stationary and slowly moving cars;
- motorcycle and tall vehicle;
- pedestrian and bicycle rejection;
- heavy rain, wind, direct sun, darkness, and wet pavement;
- back-to-back vehicles and vehicle departure;
- disconnected, stuck-active, and noisy sensor states;
- manual override and safe operator handoff.

Production hardware requires electrical protection, installation, local radio
and construction compliance, maintenance access, and restaurant approval.
