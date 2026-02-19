import json
import random
import re
import threading
import time
from typing import Dict, Tuple
from urllib.parse import urljoin


class EmailContentGenerator:
    def __init__(
        self,
        sender_name: str,
        sender_profile: str,
        style_guide: str,
        use_gemini: bool,
        gemini_api_key: str,
        gemini_model: str,
        gemini_temperature: float,
        gemini_timeout_seconds: int,
        enable_company_research: bool,
        company_research_timeout_seconds: int,
        company_research_max_chars: int,
        gemini_debug: bool,
        gemini_max_retries: int,
        gemini_retry_base_seconds: int,
        gemini_retry_max_seconds: int,
    ) -> None:
        self.sender_name = sender_name
        self.sender_profile = sender_profile.strip()
        self.style_guide = style_guide.strip()
        self.use_gemini = use_gemini
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.gemini_temperature = gemini_temperature
        self.gemini_timeout_seconds = gemini_timeout_seconds
        self.enable_company_research = enable_company_research
        self.company_research_timeout_seconds = company_research_timeout_seconds
        self.company_research_max_chars = company_research_max_chars
        self.gemini_debug = gemini_debug
        self.gemini_max_retries = gemini_max_retries
        self.gemini_retry_base_seconds = gemini_retry_base_seconds
        self.gemini_retry_max_seconds = gemini_retry_max_seconds
        self._company_research_cache: Dict[str, str] = {}
        self._cache_lock = threading.Lock()

    def generate(self, recipient: Dict[str, str]) -> Tuple[str, str]:
        if not self.use_gemini or not self.gemini_api_key:
            return self._fallback_email(recipient)

        try:
            return self._generate_with_gemini(recipient)
        except Exception as exc:
            if self.gemini_debug:
                print(f"Gemini generation failed, using fallback: {exc}")
            return self._fallback_email(recipient)

    def _generate_with_gemini(self, recipient: Dict[str, str]) -> Tuple[str, str]:
        import requests

        company_research = self._get_company_research(recipient)
        prompt = self._build_prompt(recipient, company_research)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.gemini_temperature,
                "responseMimeType": "application/json",
            },
        }

        response = self._post_with_retry(url, payload)
        data = response.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        parsed = self._safe_json_parse(text)

        subject = parsed["subject"].strip()
        body = self._format_body(parsed, recipient["name"], company_research)
        return subject, body

    def _build_prompt(self, recipient: Dict[str, str], company_research: str) -> str:
        return f"""
Create a job outreach email for this recipient.

RECIPIENT
- Name: {recipient["name"]}
- Role: {recipient["job_role"]}
- Company: {recipient["company_name"]}

SENDER PROFILE
{self.sender_profile}

STYLE GUIDE
{self.style_guide}

COMPANY FACTS (ground truth for personalization)
{company_research if company_research else "No external company facts available."}

Output strict JSON only with these keys:
{{
  "subject": "...",
  "tldr": "...",
  "value_prop": "...",
  "company_line": "...",
  "company_fact_source": "...",
  "body": "...",
  "close": "..."
}}

Constraints:
- subject <= 65 chars
- Use plain text only (no markdown)
- Mention recipient role and company naturally
- Avoid generic claims and obvious placeholders
- Only reference company facts that appear in COMPANY FACTS
- If COMPANY FACTS are missing, keep company mention concise and non-specific
- "body" must NOT include greeting lines like "Hi ...", and must NOT include sign-offs like "Best", "Thanks", sender name
- "close" must be a single CTA/closing sentence only (no "Best", no name)
- "company_line" must be exactly one sentence, directly relevant to the role/team, and grounded in COMPANY FACTS
- "company_fact_source" must be a short verbatim snippet copied from COMPANY FACTS that justifies "company_line"
- If no high-confidence, role-relevant fact exists, set both "company_line" and "company_fact_source" to empty strings
""".strip()

    def _get_company_research(self, recipient: Dict[str, str]) -> str:
        manual_context = (recipient.get("company_context") or "").strip()
        if manual_context:
            return manual_context[: self.company_research_max_chars]

        if not self.enable_company_research:
            return ""

        company_name = (recipient.get("company_name") or "").strip()
        company_website = (recipient.get("company_website") or "").strip()
        if not company_name and not company_website:
            return ""

        cache_key = f"{company_name}|{company_website}".lower()
        with self._cache_lock:
            cached = self._company_research_cache.get(cache_key)
        if cached is not None:
            return cached

        researched = self._scrape_company_context(company_name, company_website)
        researched = self._filter_research_for_role(researched, recipient)
        with self._cache_lock:
            self._company_research_cache[cache_key] = researched
        return researched

    def _scrape_company_context(self, company_name: str, company_website: str) -> str:
        import requests
        from bs4 import BeautifulSoup

        if not company_website:
            return ""

        base_url = company_website.strip()
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        pages = [base_url, urljoin(base_url, "/about"), urljoin(base_url, "/careers")]
        chunks = []

        for page_url in pages:
            try:
                response = requests.get(
                    page_url,
                    timeout=self.company_research_timeout_seconds,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                response.raise_for_status()
            except Exception:
                continue

            try:
                soup = BeautifulSoup(response.text, "html.parser")
                title = (soup.title.string or "").strip() if soup.title else ""
                description_tag = soup.find("meta", attrs={"name": "description"})
                description = (
                    description_tag.get("content", "").strip() if description_tag else ""
                )
                h1_text = " ".join(
                    [h.get_text(" ", strip=True) for h in soup.find_all("h1")[:2]]
                ).strip()
                para_text = " ".join(
                    [p.get_text(" ", strip=True) for p in soup.find_all("p")[:8]]
                ).strip()
            except Exception:
                continue

            combined = " | ".join(
                [part for part in [title, description, h1_text, para_text] if part]
            ).strip()
            if combined:
                chunks.append(f"{page_url}: {combined}")

        summary = "\n".join(chunks).strip()
        if not summary:
            return ""

        return summary[: self.company_research_max_chars]

    def _format_body(self, parsed: Dict[str, str], recipient_name: str, company_research: str) -> str:
        tldr = self._clean_line(parsed.get("tldr", "").strip())
        value_prop = self._clean_paragraph(parsed.get("value_prop", "").strip())
        body = self._clean_body(parsed.get("body", "").strip(), recipient_name)
        company_line = self._clean_line(parsed.get("company_line", "").strip())
        company_fact_source = self._clean_line(parsed.get("company_fact_source", "").strip())
        close = self._clean_line(parsed.get("close", "").strip())
        if not close:
            close = "Would you be open to a brief conversation?"

        if not self._fact_is_grounded(company_fact_source, company_research):
            company_line = ""

        company_section = f"{company_line}\n\n" if company_line else ""
        rendered = (
            f"tldr;\n{tldr}\n\n"
            f"{value_prop}\n\n"
            f"Hi {recipient_name},\n\n"
            f"{company_section}{body}\n\n"
            f"{close}\n\n"
            f"Best,\n{self.sender_name}"
        )
        return self._dedupe_adjacent_lines(rendered)

    def _safe_json_parse(self, text: str) -> Dict[str, str]:
        raw = (text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)

    def _clean_line(self, text: str) -> str:
        cleaned = self._replace_sender_placeholder(text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        lowered = cleaned.lower().strip()
        if lowered in {"best", "best,", "thanks", "thanks,", "regards", "regards,"}:
            return ""
        return cleaned

    def _clean_paragraph(self, text: str) -> str:
        cleaned = self._replace_sender_placeholder(text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def _clean_body(self, text: str, recipient_name: str) -> str:
        cleaned = self._replace_sender_placeholder(text)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        filtered = []
        for line in lines:
            lower = line.lower()
            if lower.startswith("hi "):
                continue
            if lower.startswith(f"hi {recipient_name.lower()}"):
                continue
            if lower in {"best,", "best", "thanks,", "thanks", "regards,", "regards"}:
                continue
            if lower == self.sender_name.lower():
                continue
            filtered.append(line)
        return "\n\n".join(filtered).strip()

    def _replace_sender_placeholder(self, text: str) -> str:
        return (
            text.replace("[Sender Name]", self.sender_name)
            .replace("<Sender Name>", self.sender_name)
            .replace("{Sender Name}", self.sender_name)
        )

    def _dedupe_adjacent_lines(self, text: str) -> str:
        lines = text.splitlines()
        result = []
        previous_norm = None
        for line in lines:
            norm = re.sub(r"\s+", " ", line.strip().lower())
            if norm and norm == previous_norm:
                continue
            result.append(line)
            previous_norm = norm if norm else previous_norm
        return "\n".join(result).strip()

    def _fact_is_grounded(self, fact_source: str, company_research: str) -> bool:
        if not fact_source:
            return False
        source_norm = re.sub(r"\s+", " ", fact_source.strip().lower())
        research_norm = re.sub(r"\s+", " ", (company_research or "").strip().lower())
        return bool(source_norm and research_norm and source_norm in research_norm)

    def _filter_research_for_role(self, text: str, recipient: Dict[str, str]) -> str:
        if not text:
            return ""
        role = (recipient.get("job_role") or "").lower()
        role_tokens = [t for t in re.split(r"[^a-z0-9]+", role) if len(t) > 2]
        common_tokens = [
            "product",
            "engineering",
            "engineer",
            "frontend",
            "backend",
            "platform",
            "ai",
            "cloud",
            "developer",
            "team",
            "careers",
            "mission",
        ]
        keywords = set(role_tokens + common_tokens)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        ranked = []
        for sentence in sentences:
            lower = sentence.lower()
            score = sum(1 for k in keywords if k in lower)
            if score > 0:
                ranked.append((score, sentence.strip()))
        ranked.sort(key=lambda x: x[0], reverse=True)
        selected = []
        for _, sentence in ranked[:8]:
            if sentence and sentence not in selected:
                selected.append(sentence)
        filtered = " ".join(selected).strip()
        if not filtered:
            return ""
        return filtered[: self.company_research_max_chars]

    def _post_with_retry(self, url: str, payload: Dict) -> "requests.Response":
        import requests

        last_exception = None
        for attempt in range(self.gemini_max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=self.gemini_timeout_seconds)
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status not in (429, 500, 502, 503, 504):
                    raise
                last_exception = exc
            except requests.RequestException as exc:
                last_exception = exc

            if attempt == self.gemini_max_retries:
                break

            backoff = min(
                self.gemini_retry_max_seconds,
                self.gemini_retry_base_seconds * (2**attempt),
            )
            sleep_seconds = backoff + random.uniform(0, 1)
            if self.gemini_debug:
                print(
                    f"Gemini retry {attempt + 1}/{self.gemini_max_retries} "
                    f"after {sleep_seconds:.1f}s"
                )
            time.sleep(sleep_seconds)

        raise last_exception

    def _fallback_email(self, recipient: Dict[str, str]) -> Tuple[str, str]:
        subject = f"Application for {recipient['job_role']} role at {recipient['company_name']}"
        body = f"""tldr;
I can contribute quickly as a hands-on engineer for {recipient['company_name']}.

I build reliable product features across backend, frontend, and infra with a strong focus on shipping measurable outcomes.

Hi {recipient['name']},

I wanted to reach out regarding the {recipient['job_role']} role at {recipient['company_name']}. I am interested in teams that move fast, care about product quality, and value ownership. I would be glad to share relevant projects and discuss where I can add value quickly.

If useful, I can send a short portfolio summary tailored to your current priorities.

Best,
{self.sender_name}"""
        return subject, body
