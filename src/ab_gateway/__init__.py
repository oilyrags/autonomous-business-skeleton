"""gateway service — the single ingress for agent tool calls.

Validates the principal token, routes the task profile to a (stub) model, asks
OPA to authorize, checks kill-switch state, dispatches the tool, and emits the
audit + domain events. The determinism boundary lives here. Placeholder for
slice 00; implemented from slice 01 onward.
"""
