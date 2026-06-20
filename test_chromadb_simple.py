import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import EmbeddingFunction
import os

# 创建一个临时目录用于测试
test_db_path = "test_chroma_db_simple"
os.makedirs(test_db_path, exist_ok=True)

# 定义一个简单的恒定向量嵌入函数，继承自 ChromaDB 的基类
class SimpleEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        # 为每个输入文档返回一个长度为 384 的零向量 (all-MiniLM-L6-v2 的输出维度是 384)
        # 在实际应用中，这里应该是真正的嵌入逻辑
        import numpy as np
        return [np.zeros(384, dtype=float).tolist() for _ in input]

try:
    # 1. 初始化 ChromaDB 客户端 (使用持久化存储)
    print("Initializing ChromaDB client...")
    client = chromadb.PersistentClient(path=test_db_path, settings=Settings(anonymized_telemetry=False))

    # 2. 创建或获取一个集合 (Collection)，并指定使用我们的简单嵌入函数
    print("Creating/Getting collection with simple embedding function...")
    collection_name = "test_collection_simple"
    
    # 实例化我们的嵌入函数
    simple_ef = SimpleEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=simple_ef # 使用自定义嵌入函数
    )

    # 3. 写入测试数据 (添加文档)
    print("Adding documents...")
    documents = [
        "This is the first test document about artificial intelligence.",
        "This is the second test document about machine learning.",
        "This is the third test document about data science."
    ]
    metadatas = [
        {"source": "test_doc_1", "topic": "AI"},
        {"source": "test_doc_2", "topic": "ML"},
        {"source": "test_doc_3", "topic": "DS"}
    ]
    ids = ["doc1", "doc2", "doc3"]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print("Documents added successfully.")

    # 4. 查询测试数据 (基于 ID 获取)
    print("Querying documents by ID...")
    retrieved_docs = collection.get(ids=["doc1", "doc2"])
    print(f"Retrieved documents by ID: {retrieved_docs}")

    # 5. 查询测试数据 (基于内容查询)
    # 注意：由于我们使用了零向量，所有的相似度计算结果都将是相同的。
    # 这只是为了验证基本的查询功能是否工作。
    print("Querying documents by content (using dummy embeddings)...")
    query_text = "machine learning algorithms"
    # 我们也需要为查询提供嵌入向量，这里同样使用零向量
    dummy_query_embedding = [0.0] * 384
    query_results = collection.query(query_embeddings=[dummy_query_embedding], n_results=2)
    print(f"Top 2 results for query (dummy embedding):")
    # 由于所有向量相同，距离会是0或非常接近0
    for i, (doc, metadata, distance) in enumerate(zip(query_results['documents'][0], query_results['metadatas'][0], query_results['distances'][0])):
        print(f"  {i+1}. Document ID: {query_results['ids'][0][i]}")
        print(f"     Content: {doc}")
        print(f"     Metadata: {metadata}")
        print(f"     Distance: {distance}")

    print("\nChromaDB read/write test (with simple embedding) completed successfully!")
    print("Note: Query results are based on dummy embeddings, so distances are not meaningful.")

except Exception as e:
    print(f"An error occurred during the ChromaDB test: {e}")
    import traceback
    traceback.print_exc()

finally:
    # 清理：删除测试目录 (可选)
    import shutil
    shutil.rmtree(test_db_path, ignore_errors=True)