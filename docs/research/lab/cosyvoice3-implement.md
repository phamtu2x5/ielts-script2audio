# Fun-CosyVoice3-0.5B-2512 — implement ngắn

**Model:** `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`  
**Repo code:** https://github.com/FunAudioLLM/CosyVoice  
**Chỉ chạy trên Colab** (không cài nặng local).

## 1. Cài (Colab)

```bash
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
pip install -r requirements.txt
# nếu thiếu: apt-get install sox libsox-dev
```

```python
from huggingface_hub import snapshot_download
snapshot_download(
    "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
    local_dir="pretrained_models/Fun-CosyVoice3-0.5B",
)
# ttsfrd optional
```

## 2. Chạy model

```python
import sys
sys.path.append("third_party/Matcha-TTS")
from cosyvoice.cli.cosyvoice import AutoModel
import torchaudio

cosyvoice = AutoModel(model_dir="pretrained_models/Fun-CosyVoice3-0.5B")

# A) Zero-shot: cần file giọng mẫu + lời của file mẫu
for i, out in enumerate(cosyvoice.inference_zero_shot(
    tts_text,      # = spoken_text từ Stage 2
    prompt_text,   # lời trong ref.wav
    "ref.wav",
    stream=False,
)):
    torchaudio.save(f"out_{i}.wav", out["tts_speech"], cosyvoice.sample_rate)

# B) Instruct: thêm cảm xúc / tốc độ (không sửa script đề)
for i, out in enumerate(cosyvoice.inference_instruct2(
    tts_text,
    "You are a helpful assistant. Speak slightly faster and more tense.<|endofprompt|>",
    "ref.wav",
    stream=False,
)):
    torchaudio.save(f"out_{i}.wav", out["tts_speech"], cosyvoice.sample_rate)
```

Chi tiết API: `example.py` trong repo CosyVoice.

## 3. Nối project IELTS

| Lớp | Vai trò |
|-----|---------|
| `display_text` | Script gốc — **không đổi** |
| `spoken_text` | Cách đọc chữ (`ielts-s2a prepare`) |
| `instruct` (tuỳ) | Cảm xúc / nhanh-chậm — chỉ gửi TTS |
| Voice map | `voice_profile_id` → `ref.wav` (+ lời mẫu) |

Luồng:

```text
prepare → manifest
  → mỗi segment: spoken_text + ref giọng (+ instruct nếu cần)
  → wav + report
```

## 4. Lab tối thiểu

1. GPU Colab on  
2. Cài CosyVoice + tải weight  
3. Smoke: 1 câu EN zero_shot + 1 câu “nói nhanh” (instruct2)  
4. `prepare` Part 1 trong repo ielts-script2audio  
5. Render vài segment với 2 file ref  
6. So với Kokoro (cùng spoken_text)

## 5. Lưu ý

- **Bắt buộc** có file giọng mẫu (không giống Kokoro fixed ID)  
- Cảm xúc phải **ghi lệnh** (instruct), model không tự đoán đủ  
- Tách runtime với lab Orpheus nếu kernel bẩn  
- Chưa chốt thay Kokoro; lab xong mới quyết  

## Nguồn

- https://github.com/FunAudioLLM/CosyVoice  
- https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512  
- https://funaudiollm.github.io/cosyvoice3/

## Colab pitfall: `No module named hyperpyyaml`

PyPI package name is **`HyperPyYAML`** (import: `hyperpyyaml`).

```bash
cd /content/CosyVoice
pip install -r requirements.txt
pip install HyperPyYAML modelscope torchaudio
```

Then retry `from cosyvoice.cli.cosyvoice import AutoModel`.

## Colab pitfall: `libcudart.so.13` when importing CosyVoice

Often caused by **`onnxruntime-gpu`** (needs CUDA 13), not by missing HyperPyYAML.

```bash
pip uninstall -y onnxruntime-gpu
pip install onnxruntime HyperPyYAML modelscope torchaudio
```

Then:
```python
from cosyvoice.cli.cosyvoice import AutoModel
```

CosyVoice still uses GPU via **PyTorch** for the main model; `onnxruntime` here is mainly for frontend ONNX helpers.

## Colab pitfall: `No module named whisper`

CosyVoice frontend imports OpenAI Whisper (`import whisper`).

PyPI package name is **`openai-whisper`** (not a package named `whisper` alone).

```bash
pip install openai-whisper
```

Also: `pip install -r requirements.txt` may **partially fail** on Colab (wheel build errors). Still install critical packages explicitly:

```bash
pip uninstall -y onnxruntime-gpu
pip install HyperPyYAML modelscope torchaudio onnxruntime openai-whisper
```

