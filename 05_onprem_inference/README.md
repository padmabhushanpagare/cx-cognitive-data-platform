# On-Premise Inference Optimization (Module 05)

## Overview
This module handles the deployment and optimization of open-source Large Language Models (LLMs) on local, on-premise hardware. This is critical for BPO clients who cannot send Personally Identifiable Information (PII) to third-party cloud APIs like OpenAI.

## Hardware Constraints
*   **Environment:** WSL2 Ubuntu / 16GB RAM / Integrated GPU (No dedicated NVIDIA GPU).
*   **Challenge:** Running an 8-billion parameter model on CPU-only infrastructure without severe latency.

## Optimization Strategy
1.  **4-bit Quantization:** We utilize Ollama, which downloads Llama 3.1 in a 4-bit quantized format (GGUF). This reduces the RAM footprint from ~16GB (FP16) down to ~4.7GB, allowing it to run smoothly on a 16GB machine.
2.  **Deterministic Output:** We use a custom `Modelfile` to set the `temperature` to `0`. In customer service, creativity is a bug. We need exact, repeatable answers.
3.  **Context Window Tuning:** We explicitly set `num_ctx` to `8192` to ensure the model can process long customer chat histories and large retrieved documents without forgetting the earlier context.

## Deployment
To build and run this optimized model locally:
```bash
# Build the custom optimized model
ollama create enterprise-cx-agent -f Modelfile

# Run it
ollama run enterprise-cx-agent

