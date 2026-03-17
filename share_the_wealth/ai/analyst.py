"""
AI insights via Anthropic Claude.
"""

from share_the_wealth.config import Settings


class AIAnalyst:
    MODEL = "claude-sonnet-4-20250514"
    ANALYZE_SYSTEM = (
        "You are a sharp, concise financial analyst specializing in political trading patterns "
        "and institutional positioning. Analyze portfolio mirror strategies with specific, actionable "
        "insights. Keep responses structured, use bullet points, be direct. No disclaimers unless critical."
    )
    CHAT_SYSTEM = (
        "You are a sharp financial analyst helping someone manage a mirror trading portfolio "
        "based on congressional disclosures and hedge fund 13F filings. Be specific, concise, and actionable."
    )

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or Settings.ANTHROPIC_API_KEY

    def analyze_portfolio(self, context: str) -> str:
        if not self._api_key:
            return "Set ANTHROPIC_API_KEY in .env to enable AI analysis."
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            msg = client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                system=self.ANALYZE_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        "Analyze this mirrored portfolio and give me: "
                        "1) Key themes and sector concentration, "
                        "2) Risks I should know, "
                        "3) Top conviction plays worth noting, "
                        "4) One contrarian take.\n\n"
                        f"{context}"
                    ),
                }],
            )
            return msg.content[0].text if msg.content else "No response."
        except Exception as e:
            return f"Error: {e}"

    def chat(self, context: str, messages: list[dict], new_question: str) -> str:
        if not self._api_key:
            return "Set ANTHROPIC_API_KEY in .env to enable AI chat."
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            formatted.append({
                "role": "user",
                "content": f"{new_question}\n\nPortfolio context:\n{context}",
            })
            msg = client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                system=self.CHAT_SYSTEM,
                messages=formatted,
            )
            return msg.content[0].text if msg.content else "No response."
        except Exception as e:
            return f"Error: {e}"
