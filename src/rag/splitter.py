"""DocumentSplitter — 文档分块策略。"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    """使用 RecursiveCharacterTextSplitter 按 Markdown 层级智能分块。

    chunk_size:    每个分块的最大字符数
    chunk_overlap: 相邻分块的重叠字符数（保持上下文连贯）
    separators:    按优先级尝试的分隔符（先按 ## 标题分，再按段落，再按句子）
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n## ",     # Markdown 二级标题
                "\n### ",    # 三级标题
                "\n#### ",   # 四级标题
                "\n",        # 段落
                "。",        # 中文句号
                ". ",        # 英文句号
                " ",         # 空格（最后手段）
                "",          # 逐字符分割
            ],
            keep_separator=True,  # 保留标题信息在 chunk 中
        )

    def split(self, documents: list[Document]) -> list[Document]:
        """分割文档列表，返回 chunk 列表。"""
        return self._splitter.split_documents(documents)

    def split_text(self, text: str) -> list[str]:
        """分割纯文本。"""
        return self._splitter.split_text(text)
