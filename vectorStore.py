import os
import openai
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from transformers import GPT2Tokenizer

class VectorStore:
    """
        Setup初始化OpenAI和Pinecone客户端。
        openai_key_path (str): 存储OpenAI API密钥的文件路径。
        pinecone_key_path (str): 存储Pinecone API密钥的文件路径。
        pinecone_env (str): Pinecone环境名称，默认值为"us-west1-gcp"。
        openai_client: OpenAI客户端实例。
        pinecone_index: Pinecone索引实例。

        使用: setup = Setup("openai_api.txt", "pinecone_api.txt")
        setup.openai_client
    """

    def __init__(self, openai_key_path, pinecone_key_path, pinecone_env="us-west1-gcp",index_name = "book-chapters"):
        self.openai_key_path = openai_key_path
        self.pinecone_key_path = pinecone_key_path
        self.openai_key = None
        self.pinecone_env = pinecone_env 
        self.index_name = index_name
        self.openai_client = self._load_openai() 
        self.pinecone_index = self._initialize_pinecone()
        self.namespace = None
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")  # Initialize GPT-2 tokenizer


    def _load_openai(self):
        client = None
        try:
            with open(self.openai_key_path, "r") as file:
                api_key = file.read().strip()
            os.environ["OPENAI_API_KEY"] = api_key
            openai.api_key = api_key
            client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error reading OpenAI API key: {e}")
        return client

    def _initialize_pinecone(self):
        try:
            with open(self.pinecone_key_path, "r") as file:
                self.pinecone_key = file.read().strip()
                pinecone.init(api_key=self.pinecone_key, environment="us-west1-gcp")

            index_name = "book-chapters"
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(index_name, dimension=1536)  # dimension matches OpenAI embedding size
                print(f"-----Created and connected to index: {index_name}-----")
            else:
                print(f"-----Connected to index: {index_name}-----")
            return pinecone.Index(index_name)
        except Exception as e:
            print(f"An error occurred during Pinecone initialization: {e}")



    # def openai_chat(self, system_prompt, user_prompt, model="gpt-4", max_tokens=4000, temperature=0.7):
    #     try:
    #         response = openai.chat.completions.create(
    #             model=model,
    #             messages=[
    #                 {"role": "system", "content": system_prompt},
    #                 {"role": "user", "content": user_prompt}
    #             ],
    #             max_tokens=max_tokens,
    #             temperature=temperature,
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"An error occurred during OpenAI chat completion: {e}")
    #         return None

    def create_namespace(self, title):
        self.namespace = title.replace(" ", "_").lower() # for consistency
        print(f"Namespace created: {self.namespace}")
        return self.namespace

    def get_embedding(self, text):
        try:
            embed = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            embeds = embed.embed_query(text)
            return embeds
        except Exception as e:
            print(f"An error occurred while fetching the embedding: {e}")
            return None

    def upsert_embedding(self, vector_id, text, override_mode = True):
        if (not override_mode) and self._vector_exists(vector_id): # 保护存储
            print(f"Vector with ID {vector_id} already exists. Skipping upsert.")
            return

        embedding = self.get_embedding(text)
        try:
            self.pinecone_index.upsert(vectors=[(vector_id, embedding)], namespace=self.namespace)
            print(f"Safely upserted embedding with ID {vector_id} in namespace {self.namespace}.")
        except Exception as e:
            print(f"Error upserting embedding in Pinecone: {e}")


    def _vector_exists(self, vector_id):
        try:
            response = self.pinecone_index.fetch(ids=[vector_id], namespace=self.namespace)
            return vector_id in response['vectors']
        except Exception as e:
            print(f"An error occurred during vector existence check: {e}")
            return False

    def retrieve_embedding(self, vector_id):
        try:
            response = self.pinecone_index.fetch(ids=[vector_id], namespace=self.namespace)
            if response and "vectors" in response and vector_id in response["vectors"]:
                vector = response["vectors"][vector_id]["values"]
                return vector
            else:
                return "Draft not found"
        except Exception as e:
            print(f"An error occurred during embedding retrieval: {e}")
            return None


    def split_by_batches(self,text,batch_size = 1500):
        texts = []
        metadatas = []
        for i in tqdm(range(0, len(text), batch_size)):
            # get end of batch
            i_end = min(len(text), i+batch_size)
            batch = data.iloc[i:i_end]



            # first get metadata fields for this record
            # metadatas = [{
            #     'title': record['title'],
            #     'text': record['context']
            # } for j, record in batch.iterrows()]
            # get the list of contexts / documents


            documents = batch['context']
            # create document embeddings
            embeds = embed.embed_documents(documents)
            # get IDs
            ids = batch['id']
            # add everything to pinecone
            index.upsert(vectors=zip(ids, embeds, metadatas))

    def split_text(self, title, text, max_length=20):
            # 文本是否包含中文字符
            if self.is_chinese(text):
                return self.split_text_chinese(title, text, max_length)
            else:
                return self.split_text_english(title, text, max_length)

    def is_chinese(self, text):
        for char in text:
            if '\u4e00' <= char <= '\u9fff': # within Chinese Unicode range
                return True
        return False

    def split_text_chinese(self, title, text, max_length=20):
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_count = 1  # 初始化块计数器

        for char in text:
            # 超过最大长度则分割
            if current_length + len(char) + 1 > max_length:
                chunk_title = f"{title}_{chunk_count}"  # 生成当前块的标题
                chunks.append((chunk_title, "".join(current_chunk)))  # 添加元组 (标题, 文本块)
                current_chunk = [char]
                current_length = len(char) + 1
                chunk_count += 1  # 增加块计数器
            else:
                current_chunk.append(char)
                current_length += len(char) + 1

        if current_chunk:
            chunk_title = f"{title}_{chunk_count}"  # 生成最后一块的标题
            chunks.append((chunk_title, "".join(current_chunk)))
        
        return chunks

    def split_text_english(self, title, text, max_length=20):
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_count = 1  # 初始化块计数器

        for word in words:
            # 超过最大长度则分割
            if current_length + len(word) + 1 > max_length:
                chunk_title = f"{title}_{chunk_count}"  # 生成当前块的标题
                chunks.append((chunk_title, " ".join(current_chunk)))  # 添加元组 (标题, 文本块)
                current_chunk = [word]
                current_length = len(word) + 1
                chunk_count += 1  # 增加块计数器
            else:
                current_chunk.append(word)
                current_length += len(word) + 1

        if current_chunk:
            chunk_title = f"{title}_{chunk_count}"  # 生成最后一块的标题
            chunks.append((chunk_title, " ".join(current_chunk)))
        
        return chunks



    def calculate_tokens(self, text):
        tokens = self.tokenizer.tokenize(text)
        return len(tokens)
    
    def calculate_tokens_chinese(self, text):
        tokens = list(text)
        return len(tokens)


    def insert_to_pinecone(self, text):
        # if only book name is given, create a namespace
        if len(text) == 1:
            self.create_namespace(text[0])
            return


        vector_store.create_namespace(data['title'])
        
        # Split the text
        chunks = vector_store.split_text(data['title'], data['content'], max_length=1500)
        
        # Upsert each chunk
        for chunk_title, chunk in chunks:
            metadata = data['context']
            text_with_metadata = f"{chunk}\n\nContext: {metadata}"
            vector_store.upsert_embedding(chunk_title, text_with_metadata)