from openai import OpenAI
from linkpilot.config import get_settings

class DraftService:
    def __init__(self):
        cfg = get_settings()
        if not cfg.llm_api_key or not cfg.llm_model:
            raise RuntimeError("Set LLM_API_KEY and LLM_MODEL in .env using your 9Router dashboard values.")
        self.client = OpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key,
                             timeout=45.0, max_retries=1)
        self.model = cfg.llm_model

    def generate(self, prospect: dict) -> str:
        system = (
            "Write concise, truthful professional networking notes. Never invent shared history, "
            "familiarity, achievements, vacancies or facts. Use only supplied professional context. "
            "Do not imply the sender knows the recipient. Return one respectful natural note, ideally "
            "under 250 characters."
        )
        user = f"""
Recipient: {prospect['full_name']}
Company: {prospect['company']}
Title: {prospect['title']}
Category: {prospect['category']}
Professional context: {prospect.get('research_notes') or 'No additional context supplied.'}

Sender background:
- 10+ years in data analytics and business intelligence
- Power BI, SQL, Excel, reporting and automation
- Exploring relevant BI and Data Analytics opportunities in India

Tailor the note to the recipient's role. For Recruiter, TA or HR, introduce relevant experience
and interest in suitable BI opportunities. For hiring managers and data leaders, emphasize
analytics, reporting and automation value. For senior executives, be concise and focus on
business intelligence value. Never fabricate facts or imply an existing relationship.
"""
        result = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.55, max_tokens=160,
        )
        text = result.choices[0].message.content
        if not text or not text.strip():
            raise RuntimeError("The configured model returned an empty response.")
        return text.strip().strip('"')
