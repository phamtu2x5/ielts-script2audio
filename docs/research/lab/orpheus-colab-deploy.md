# Orpheus on Colab — deploy notes (from docs + lab failures)

## Official deployment (upstream)

Source: [canopyai/Orpheus-TTS README](https://github.com/canopyai/Orpheus-TTS)

```bash
pip install orpheus-speech   # pulls vLLM
pip install vllm==0.7.3      # upstream pin; package built for vllm<=0.7.3
```

Python API (local open-weight):

```python
from orpheus_tts import OrpheusModel
model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod", max_model_len=2048)
for chunk in model.generate_speech(prompt=text, voice="tara"):
    ...
# wav: mono int16, 24000 Hz
```

Voices (finetune-prod): `tara, leah, jess, leo, dan, mia, zac, zoe`.

Official Colab: https://colab.research.google.com/drive/1KhXT56UePPUHhqitJNUxq63k-pQomz3N

**Not** the paid path: `pip install orpheus-tts` + API key.

## Why Colab installs feel very slow

| Step | What downloads | Why long |
|------|----------------|----------|
| `orpheus-speech` | package + dependency tree | resolves vLLM/torch stack |
| `vllm==0.7.3` | large CUDA wheels | hundreds of MB–GB |
| First `OrpheusModel(...)` | HF weights finetune-prod (~3B-class) | multi-GB download once per runtime |
| Colab image already full | pip conflict noise | resolver prints many unrelated conflicts |

Slow **pip** ≠ model generating audio yet. First successful load is the heavy step.

## Failures seen in our notebook outputs (chronology)

1. **`libcudart.so.13`** — vLLM wheel linked to CUDA 13; Colab often CUDA 12.x → pin `vllm==0.7.3`.
2. **`numpy.dtype size changed`** — mixed NumPy 1.x/2.x binary extensions after force reinstalls without Restart.
3. **`cannot import name '_Ink' from PIL._typing`** — Pillow/torchvision version skew after pip churn (traceback goes torchvision → PIL).
4. Log also showed **`cuda_available False`** in one run — GPU not attached or lost after bad install; must re-select GPU runtime.
5. Log showed **numpy printed 2.0.2 after we pinned 1.26.4** — another package upgraded NumPy again, or cell order/restart issue.

`FileNotFoundError: lab_render_report.json` is only a **follow-on**: render never started.

## Recovery procedure that matches docs + Colab reality

1. Runtime → **Disconnect and delete runtime** (cleanest if ABI already broken).
2. New runtime → **GPU on** (confirm in UI).
3. Clone/pull repo.
4. Run **one** install cell (orpheus-speech + vllm==0.7.3 + pin numpy/pillow).
5. If import fails → **Restart session** once (unload old .so) → re-run install **or** only import check if packages already OK.
6. Only then prepare + render (`--limit 4` on T4).

Ignore most pip warnings about google-adk/cuml/jax/opencv **unless** `from orpheus_tts import OrpheusModel` still fails.

## Project integration

- Stage 1–2: `ielts-s2a prepare` → manifest (unchanged).
- Lab: `scripts/lab_render_orpheus_from_manifest.py` maps `voice_profile_id` → tara/leo.
- Do not install this stack on the user laptop ([[feedback-no-heavy-local-packages]]).


## Hard rule for `numpy.dtype size changed`

**Do not import vllm/Orpheus in the same kernel session immediately after `pip install --force-reinstall numpy`.**

Binary extensions already loaded in the process keep the old ABI. Symptoms:

```text
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

### Fix that actually works on Colab

1. Run **install-only** cell (pip only).
2. **Runtime → Restart session** (or Disconnect and delete runtime if repeated failures).
3. Run **import-check** cell (import numpy/torch/vllm/OrpheusModel only).
4. Only then prepare + render.

If import still fails after restart: **Delete runtime**, new GPU, full reinstall once, restart once, import once.

Pin used in project notebook: `numpy==1.26.4`, `vllm==0.7.3`, `pillow==10.4.0`, package `orpheus-speech` (not `orpheus-tts`).

