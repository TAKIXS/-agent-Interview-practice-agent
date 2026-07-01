"""DocumentLoader — 加载 knowledge_base 中所有 Markdown 文件。"""

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document


class DocumentLoader:
    """递归加载 knowledge_base/ 下所有 .md 文件，标记主题分类元数据。"""

    def __init__(self, base_path: str = "data/knowledge_base") -> None:
        self._base = Path(base_path)
        if not self._base.exists():
            raise FileNotFoundError(f"知识库目录不存在: {self._base.resolve()}")

    def load_all(self) -> list[Document]:
        """加载全部 MD 文档，自动打上 category 元数据标签。"""
        loader = DirectoryLoader(
            path=str(self._base),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=False,
        )
        docs = loader.load()

        for doc in docs:
            source = Path(doc.metadata.get("source", ""))
            # 从路径提取 category：例如 java_core → java
            category = self._extract_category(source)
            doc.metadata["category"] = category
            doc.metadata["filename"] = source.name

        return docs

    @staticmethod
    def _extract_category(path: Path) -> str:
        """从文件路径提取主题分类。

        data/knowledge_base/java_core/01_xxx.md → java_core
        """
        # 父目录名即为分类
        return path.parent.name

    def load_by_category(self, category: str) -> list[Document]:
        """只加载指定分类的文档。"""
        all_docs = self.load_all()
        return [d for d in all_docs if d.metadata.get("category") == category]

    @property
    def categories(self) -> list[str]:
        """返回所有分类名。"""
        return [
            d.name for d in self._base.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
