from typing import List, Dict, Any
import os, chromadb
DB_DIR=os.environ.get("RAG_DB_DIR","/data/index"); COLLECTION="homelab_docs"
client=chromadb.PersistentClient(path=DB_DIR)
if COLLECTION not in [c.name for c in client.list_collections()]: coll=client.create_collection(COLLECTION, metadata={"hnsw:space":"cosine"})
else: coll=client.get_collection(COLLECTION)
def add_docs(docs:List[str], metadatas:List[Dict[str,Any]]):
  ids=[f"doc_{i}_{abs(hash(d))}" for i,d in enumerate(docs)]; coll.add(documents=docs, metadatas=metadatas, ids=ids); return ids
def query(q:str,k:int=5):
  res=coll.query(query_texts=[q], n_results=k); items=[]
  for i in range(len(res["documents"][0])):
    items.append({"document":res["documents"][0][i],"metadata":res["metadatas"][0][i],"id":res["ids"][0][i]})
  return items
