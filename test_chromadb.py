import chromadb
from chromadb.config import Settings
import os

# 创建一个临时目录用于测试
test_db_path = "test_chroma_db"
os.makedirs(test_db_path, exist_ok=True)

try:
    # 1. 初始化 ChromaDB 客户端 (使用持久化存储)
    print("Initializing ChromaDB client...")
    client = chromadb.PersistentClient(path=test_db_path, settings=Settings(anonymized_telemetry=False))

    # 2. 创建或获取一个集合 (Collection)
    print("Creating/Getting collection...")
    collection_name = "test_collection"
    collection = client.get_or_create_collection(name=collection_name)

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
    print("Querying documents by content...")
    query_text = "machine learning algorithms"
    query_results = collection.query(query_texts=[query_text], n_results=2)
    print(f"Top 2 results for query '{query_text}':")
    for i, (doc, metadata, distance) in enumerate(zip(query_results['documents'][0], query_results['metadatas'][0], query_results['distances'][0])):
        print(f"  {i+1}. Document ID: {query_results['ids'][0][i]}")
        print(f"     Content: {doc}")
        print(f"     Metadata: {metadata}")
        print(f"     Distance: {distance}")

    print("\nChromaDB read/write test completed successfully!")

except Exception as e:
    print(f"An error occurred during the ChromaDB test: {e}")
    import traceback
    traceback.print_exc()

finally:
    # 清理：删除测试目录 (可选，但为了测试环境干净)
    # 注意：在实际应用中，你可能不想删除数据库文件
    # import shutil
    # shutil.rmtree(test_db_path, ignore_errors=True)
    pass