# External API Keys Documentation

---

## 🚨 IMPORTANT - API Key Storage Rules

**ALWAYS store API keys in environment files, never commit to Git:**

1. **Local Development:** Add to `backend/.env` 
2. **Production:** Add to Railway/Vercel environment dashboards
3. **NEVER:** Commit API keys to Git repository
4. **SECURITY:** Regularly rotate API keys for security

**Template for .env file:**
```bash
# Copy this structure, but NEVER commit actual keys
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
SCREENSHOT_API_KEY=
```

---

## Azure OpenAI (GPT-5.1)

**Purpose:** LLM pro překlady a generování obsahu ve Webomat

**Configuration:**
- API Key: [SET IN ENVIRONMENT]
- Endpoint: `https://pilot-project-sweden.cognitiveservices.azure.com/`
- API Version: `2024-12-01-preview`
- Deployment Name: `go-gpt-5.1`
- Model: GPT-5.1

**Usage:** 
- Automatické překlady webů (česko → angličtina)
- Generování obsahu
- Textové úpravy

**Environment Variables:**
```
AZURE_OPENAI_API_KEY=[SET_IN_ENVIRONMENT]
AZURE_OPENAI_ENDPOINT=https://pilot-project-sweden.cognitiveservices.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=go-gpt-5.1
```

## Screenshot API

**Purpose:** Screenshoty konkurenčních webů pro inspiraci a analýzu

**Provider:** Screenshot-API.org

**Configuration:**
- API Key: [SET IN ENVIRONMENT]
- Base URL: `https://api.screenshot-api.org/api/v1/screenshot`

**Usage Example:**
```javascript
const screenshot = await fetch(
  "https://api.screenshot-api.org/api/v1/screenshot",
  {
    method: "POST",
    headers: {
      "Authorization": "Bearer [SET_IN_ENVIRONMENT]",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      url: "https://example.com",
      format: "png",
      fullPage: true
    })
  }
);

const { data } = await screenshot.json();
console.log(data.screenshotUrl);
```

**Environment Variables:**
```
SCREENSHOT_API_KEY=[SET_IN_ENVIRONMENT]
SCREENSHOT_API_URL=https://api.screenshot-api.org/api/v1/screenshot
```

## Future Implementation

### Screenshot API Integration Plan

1. **CRM Business Details Page**
   - Přidat tlačítko "Získat screenshot konkurence"
   - UI pro zadání URL konkurenčních webů
   - Zobrazení screenshotů jako carousel/gallery

2. **Website Generation Workflow**
   - Automatické screenshoty požadovaných inspirativních webů
   - Store v Supabase Storage jako reference

3. **Marketing Tools**
   - Screenshoty pro marketingové analýzy
   - Compare tools pro A/B testing

### Azure OpenAI Integration Status

✅ **Done:**
- Basic Azure OpenAI client setup
- Translation functions updated
- Environment variables configured

🔄 **TODO:**
- Test functionality with real GPT-5.1 model
- Add error handling and retry logic
- Integrate with website generation workflow
- Add content generation features