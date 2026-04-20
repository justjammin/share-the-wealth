"""
AI insights via Anthropic Claude. Optional local RAG (sentence-transformers) for grounded retrieval.
"""

from share_the_wealth.ai.local_embeddings import is_available as _rag_available
from share_the_wealth.ai.rag_retriever import get_rag_retriever
from share_the_wealth.config import Settings

_RAG_DISCLAIMER = (
    "Informational only; not financial advice. Ground answers in the retrieved excerpts when applicable."
)


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
    CHAT_SYSTEM_RAG = (
        CHAT_SYSTEM + " "
        "When RETRIEVED EXCERPTS are provided, prioritize them for factual claims about this portfolio; "
        "if excerpts do not answer the question, say so and use the full context below."
    )

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or Settings.ANTHROPIC_API_KEY

    def _rag_block(self, context: str, query: str) -> str | None:
        if not Settings.USE_LOCAL_RAG or not _rag_available():
            return None
        retriever = get_rag_retriever()
        retriever.ensure_indexed(context)
        chunks = retriever.retrieve(query)
        if not chunks:
            return None
        return "\n\n---\n\n".join(chunks)

    def analyze_portfolio(self, context: str) -> str:
        if not self._api_key:
            return "Set ANTHROPIC_API_KEY in .env to enable AI analysis."
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            rag_query = (
                "portfolio themes sector concentration risks political trading "
                "hedge fund conviction holdings"
            )
            excerpts = self._rag_block(context, rag_query)
            body = (
                "Analyze this mirrored portfolio and give me: "
                "1) Key themes and sector concentration, "
                "2) Risks I should know, "
                "3) Top conviction plays worth noting, "
                "4) One contrarian take.\n\n"
            )
            if excerpts:
                body += f"Retrieved excerpts (local embeddings, RAG):\n{excerpts}\n\n---\n\nFull portfolio data:\n{context}"
            else:
                body += context
            body += f"\n\n{_RAG_DISCLAIMER}"
            msg = client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                system=self.ANALYZE_SYSTEM,
                messages=[{"role": "user", "content": body}],
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
            excerpts = self._rag_block(context, new_question)
            system = self.CHAT_SYSTEM_RAG if excerpts else self.CHAT_SYSTEM
            user_tail = (
                f"Retrieved excerpts (local embeddings, RAG):\n{excerpts}\n\n---\n\n"
                f"Full portfolio context:\n{context}\n\n---\n\n"
                f"Question: {new_question}\n\n{_RAG_DISCLAIMER}"
                if excerpts
                else f"{new_question}\n\nPortfolio context:\n{context}"
            )
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            formatted.append({"role": "user", "content": user_tail})
            msg = client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                system=system,
                messages=formatted,
            )
            return msg.content[0].text if msg.content else "No response."
        except Exception as e:
            return f"Error: {e}"
