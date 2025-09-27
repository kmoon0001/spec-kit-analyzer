        self.faiss_index.add(embeddings)
        self.is_index_ready = True
        logger.info(f"Successfully indexed {len(self.chunks)} document chunks.")
    def search(
        self, query: str, top_k: int = 5, metadata_filter: dict | None = None
    ) -> list[dict]:
        """
        Performs a FAISS similarity search through the document chunks.
        Args:
            query (str): The search query.
            top_k (int): The number of top results to return.
            metadata_filter (dict): A dictionary to filter chunks by metadata before searching.
        Returns:
            list[dict]: A list of the top matching chunks.
        """
        if not self.is_index_ready or not self.faiss_index:
            logger.warning("Search called before the index was ready.")
            return []
        # 1. Pre-filtering (if a filter is provided)
        candidate_chunks = self.chunks
        if metadata_filter:
            candidate_chunks = [
                chunk
                for chunk in self.chunks
                if all(
                    item in chunk["metadata"].items()
                    for item in metadata_filter.items()
                )
            ]
        if not candidate_chunks:
            return []  # No chunks matched the filter
        # 2. Embedding and Searching
        query_embedding = self.model.encode([query])
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        search_k = top_k * 3 if metadata_filter else top_k
        _distances, indices = self.faiss_index.search(query_embedding, search_k)
        # 3. Post-filtering and result assembly
        results = []
        # Get the indices of the candidate chunks for quick lookup
        candidate_indices = {
            i for i, chunk in enumerate(self.chunks) if chunk in candidate_chunks
        }
        for i in indices[0]:
            if i != -1 and i in candidate_indices:
                results.append(self.chunks[i])
                if len(results) == top_k:
                    break
        return results
