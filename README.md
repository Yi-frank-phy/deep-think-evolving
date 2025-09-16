<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1U-U3t01354eboQIODrLozKjWCIYQYWwP

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Validate the AI pipeline environment

To confirm that the Gemini API key and local Ollama embedding service are
configured correctly, install the Python dependencies and execute the smoke
tests:

```bash
pip install -r requirements.txt
pytest -k smoke
```

The smoke suite exercises the strategic blueprint generation, embedding, and
similarity calculation pipeline, and will skip automatically if any required
service is unavailable.

To run the pipeline without a local Ollama instance, enable mock embeddings by
setting the `USE_MOCK_EMBEDDING` environment variable:

```bash
USE_MOCK_EMBEDDING=1 pytest -k smoke
```

The same flag applies when invoking the Python entry point directly:

```bash
USE_MOCK_EMBEDDING=1 python main.py
```
