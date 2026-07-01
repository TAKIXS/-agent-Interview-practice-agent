"""Retriever — MMR 检索 + 元数据过滤。"""

from __future__ import annotations
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class Retriever:
    """基于 ChromaDB 的 MMR 检索器，支持按 category 过滤。

    MMR (Maximal Marginal Relevance)：
    - 平衡结果的相关性和多样性
    - fetch_k 先拉取更多候选，再通过 MMR 挑选 k 个最终结果
    """

    def __init__(
        self,
        vectorstore: Chroma,
        k: int = 6,
        fetch_k: int = 20,
    ) -> None:
        self._vectorstore = vectorstore
        self._k = k
        self._fetch_k = fetch_k

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        k: int | None = None,
    ) -> list[Document]:
        """检索最相关的文档 chunk。

        Args:
            query:    查询文本
            category: 可选的主题过滤（如 'java_core', 'agent_fundamentals'）
            k:        返回数量（默认使用初始化值）
        """
        retriever = self._build_retriever(k or self._k)

        if category:
            retriever.search_kwargs["filter"] = {"category": category}

        return retriever.invoke(query)

    def retrieve_with_scores(
        self,
        query: str,
        category: str | None = None,
    ) -> list[tuple[Document, float]]:
        """检索并返回相似度分数。"""
        k = self._k
        if category:
            results = self._vectorstore.similarity_search_with_relevance_scores(
                query, k=k, filter={"category": category},
            )
        else:
            results = self._vectorstore.similarity_search_with_relevance_scores(
                query, k=k,
            )
        return results

    @property
    def categories(self) -> list[str]:
        """返回向量库中所有 category 值。"""
        # 从存储的元数据中提取
        collection = self._vectorstore.get()
        metadatas = collection.get("metadatas", [])
        cats: set[str] = set()
        for m in metadatas:
            if m and "category" in m:
                cats.add(m["category"])
        return sorted(cats)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _build_retriever(self, k: int) -> BaseRetriever:
        """构建 MMR 检索器。"""
        return self._vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": self._fetch_k,
            },
        )
