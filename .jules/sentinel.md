## 2025-05-22 - Exposed API Key in Vite Config
**Vulnerability:** The `vite.config.ts` file used `define` to inject `GEMINI_API_KEY` into the client-side bundle as `process.env.API_KEY`.
**Learning:** Even if the frontend code doesn't explicitly use the variable, `define` performs a literal replacement during build. If the code *did* reference it (or if an attacker found the bundled string), the backend secret would be exposed to the public.
**Prevention:** Never use `define` to pass backend secrets to the frontend. Use `VITE_` prefix only for public config, and keep secrets strictly on the server.
