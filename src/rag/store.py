"""VectorStoreManager — ChromaDB 向量库全生命周期管理。

功能：
- 首次运行：自动从 MD 文档构建向量库（索引管道）
- 后续运行：直接加载已有向量库（跳过重复索引）
- 提供重建能力：删除旧库 → 重新构建
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class VectorStoreManager:
    """管理 ChromaDB 向量库的创建、加载和重建。"""

    def __init__(
        self,
        persist_dir: str,
        embedding: Embeddings,
    ) -> None:
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._embedding = embedding

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def get_or_create(self) -> Chroma:
        """智能获取向量库：已存在则加载，不存在则自动构建索引。"""
        if self._already_indexed():
            return self._load()
        else:
            return self._build_from_scratch()

    def rebuild(self) -> Chroma:
        """强制重建索引（删除旧向量库后重新构建）。"""
        self._delete()
        return self._build_from_scratch()

    @property
    def persist_dir(self) -> str:
        return str(self._persist_dir)

    # ------------------------------------------------------------------
    # 内部 — 索引管道
    # ------------------------------------------------------------------

    def _build_from_scratch(self) -> Chroma:
        """完整索引管道：加载文档 → 分割 → 向量化 → 持久化。"""
        from src.rag.loader import DocumentLoader
        from src.rag.splitter import DocumentSplitter

        loader = DocumentLoader()
        docs = loader.load_all()
        print(f"[VectorStore] 加载 {len(docs)} 篇文档")

        splitter = DocumentSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split(docs)
        print(f"[VectorStore] 分割为 {len(chunks)} 个 chunk")

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self._embedding,
            persist_directory=str(self._persist_dir),
        )
        print(f"[VectorStore] 索引完成，持久化到 {self._persist_dir}")
        return vectorstore

    def _load(self) -> Chroma:
        """加载已有向量库。"""
        return Chroma(
            persist_directory=str(self._persist_dir),
            embedding_function=self._embedding,
        )

    def _already_indexed(self) -> bool:
        """检查向量库是否已构建。"""
        return (
            self._persist_dir.exists()
            and any(self._persist_dir.iterdir())
        )

    def _delete(self) -> None:
        """删除向量库目录。"""
        import shutil
        if self._persist_dir.exists():
            shutil.rmtree(self._persist_dir)
            print(f"[VectorStore] 已删除旧向量库: {self._persist_dir}")
