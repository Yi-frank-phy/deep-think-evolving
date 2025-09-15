<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1U-U3t01354eboQIODrLozKjWCIYQYWwP

## Run Locally

**Prerequisites:** Node.js for the web client and Python 3.11+ for the CLI helpers.

### Front-end

1. Install dependencies: `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app: `npm run dev`

### Python tooling & demos

1. Install Python dependencies: `pip install -r requirements.txt`
2. Export your Gemini API key in the current shell before running scripts:
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   ```
3. Run the end-to-end demo: `python main.py`

## Configuration & Services

### Gemini / Google API key setup

1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Create or reuse an API key with access to Gemini 1.5 models and Google Search Grounding.
3. Copy the key and either:
   * Place it in `.env.local` (front-end) or `.env` (if you maintain one for Python), **and**
   * Export it as an environment variable for Python scripts:
     ```bash
     export GEMINI_API_KEY="your_gemini_api_key"
     ```
4. Restart your terminal or re-run the export whenever the variable is missing. The Python demo prints actionable errors if the key is not detected or is invalid.

### Google Search Grounding prerequisites

* Ensure the API key you generated above has the *Google Search Grounding* add-on enabled in Google AI Studio. Without this entitlement the demo call will fail with an authentication error.
* `google-generativeai` (installed via `requirements.txt`) is required. Keep it updated to the latest release to receive the Grounding client APIs.
* Network access to `generativelanguage.googleapis.com` must be allowed.

### Local Ollama embedding service

1. [Install Ollama](https://ollama.com/) on your machine.
2. Pull the embedding model used by this repo:
   ```bash
   ollama pull dengcao/Qwen3-Embedding-8B:Q4_K_M
   ```
3. Start the Ollama server (if not already running):
   ```bash
   ollama serve
   ```
4. By default the embedding script expects Ollama at `http://localhost:11434`. Update `src/embedding_client.py` if you host it elsewhere.

When either Ollama or Google services are unreachable the Python utilities emit explicit guidance to help you troubleshoot network connectivity or missing configuration.
