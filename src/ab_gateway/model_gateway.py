"""Model gateway — the single ingress + determinism boundary.

Slice 01 binds every task profile to a deterministic stub model. Real providers
(vLLM / managed) slot in behind this same function later without changing callers.
Decision content is NEVER taken from model output — the gateway only uses the
stub to exercise the boundary; deterministic logic produces the actual result.
"""


def complete(task_profile: str, prompt: str) -> str:
    return f"[stub:{task_profile}] {prompt}"
