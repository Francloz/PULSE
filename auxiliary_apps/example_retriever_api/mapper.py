import os
import pandas as pd
import os
import torch
import requests
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel
import spacy

concept_directory = "./data/"

concept_df = pd.read_csv(os.path.join(concept_directory, 'CONCEPT.csv'), dtype=str, delimiter='\t')
# Filter for relevant domains and only standard concepts
relevant_domains = ["Condition", "Drug", "Procedure", "Measurement",
                    "Observation", "Unit", "Gender", "Race", "Ethnicity",
                    "Meas Value"]  # "Value-as-Concept" corresponds to "Meas Value" domain
filtered_concept_df = concept_df[
    # concept_df['domain_id'].isin(relevant_domains) &
    # (concept_df['standard_concept'] == 'S') &
    (concept_df["vocabulary_id"].isin(["SNOMED", "CDM", "LOINC", "GENDER", "UCUM", "Ethnicity", "Race", "LOINC", 'ATC']))
][["concept_id", "concept_code", "concept_name", "vocabulary_id"]]
concept_df["vocabulary_id"].unique()
concept_df["domain_id"].unique()

concept_df[concept_df["domain_id"] == "Meas Value"]["concept_name"].unique()
filtered_concept_df["vocabulary_id"].unique()
ALL_CONCEPTS = concept_df

class BioBERTEntityLinker:
    def __init__(self, model_name="dmis-lab/biobert-base-cased-v1.1", top_k=5, debug=False, index_file="./data/concept_index.faiss"):
        """
        Initializes the BioBERT-based UMLS Entity Linker.
        - Loads BioBERT model and tokenizer.
        - Creates spaCy Doc extensions for CUI and score.
        - top_k: number of best candidates to return.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to("cpu")
        self.model.eval()
        self.top_k = top_k
        self.debug = debug
        # We will build the FAISS index on first run
        self.index = None
        self.concepts = []  # list of (CUI, name) corresponding to index entries
        self.index_file = index_file


        if os.path.exists(self.index_file):
            for concept_id, concept_name in zip(ALL_CONCEPTS['concept_id'], ALL_CONCEPTS['concept_name']):
                self.concepts.append((concept_id, concept_name))

            self.index = faiss.read_index(self.index_file)
            torch.cuda.empty_cache()
            print("Cache FAISS database loaded")

    def _get_concept_text(self, concept_id):
        defs = ALL_CONCEPTS[ALL_CONCEPTS["concept_id"] == concept_id]["concept_name"]
        return " ; ".join(set(defs)) or ""

    def build_index(self):
        """
        Build the FAISS index of all UMLS concepts used (maybe all in MRCONSO).
        For demonstration, we build from a small set or on-the-fly.
        In practice, parse MRCONSO/MRDEF or use API for a large set.
        """
        if os.path.exists(self.index_file):
            return None # The index already exists and it should be loaded


        # Example: Pre-load a small set of concepts for demo
        self.concepts = []
        embeddings = []
        from tqdm import tqdm

        BATCH_SIZE = 2**12  # Tune as needed for memory
        texts = []
        cuids = []

        for concept_id, concept_name in zip(ALL_CONCEPTS['concept_id'], ALL_CONCEPTS['concept_name']):
            if concept_name:
                texts.append(str(concept_name))
                cuids.append(concept_id)


        # Batch tokenization

        tok_batches = [texts[i:i+BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
        cuid_batches = [cuids[i:i+BATCH_SIZE] for i in range(0, len(cuids), BATCH_SIZE)]
        if self.debug:
            tok_batches = tok_batches[:10]
            cuid_batches = cuid_batches[:10]

        self.model.to(self.device)
        for text_batch, cuid_batch in tqdm(zip(tok_batches, cuid_batches), total=len(tok_batches), desc="Processing CUIs", unit="batch"):
            toks = self.tokenizer.batch_encode_plus(
                text_batch,
                return_tensors="pt",
                max_length=20,
                truncation=True,
                padding=True  # Necessary for batch input
            )
            toks = {k: v.to(self.device) for k, v in toks.items()}
            with torch.no_grad():
                out = self.model(**toks)
                embs = out.last_hidden_state[:, 0, :]  # CLS token for each input
                embs = embs / embs.norm(dim=1, keepdim=True)  # L2 normalize
            vecs = embs.cpu().numpy()
            embeddings.extend(vecs)
            self.concepts.extend(zip(cuid_batch, text_batch))
        self.model.to("cpu")

        # Stack and create FAISS index
        if embeddings:
            mat = np.vstack(embeddings).astype(np.float32)
            dim = mat.shape[1]
            self.index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine
            self.index.add(mat)
            faiss.write_index(self.index, self.index_file)

        torch.cuda.empty_cache()
        return None

    def link(self, text):
        """
        Link a text mention to OMOP CDM Concepts.
        Returns a list of (Concept_id, score) for top_k candidates.
        """
        # If index not built, build it (or update with new concepts)
        self.model.to("cpu")
        if self.index is None:
            self.build_index()

        # Step 2: Encode mention
        toks = self.tokenizer.encode_plus(text, return_tensors="pt", max_length=30, truncation=True)
        for k,v in toks.items():
            toks[k] = v.to("cpu")
        with torch.no_grad():
            out = self.model(**toks)
            mention_emb = out.last_hidden_state[:,0,:]  # CLS
            mention_emb = mention_emb / mention_emb.norm(dim=1, keepdim=True)

        query_vec = mention_emb.cpu().numpy().astype(np.float32)  # shape (1, dim)

        # 2. Search FAISS index for the top k matches (here k=1)
        distances, indices = self.index.search(query_vec, self.top_k)

        # 3. Retrieve your metadata (CUI + text) for the best hit
        results = []
        for i in range(self.top_k):
            idx = indices[0, i]
            score = distances[0, i]
            cui, text = self.concepts[idx]
            results.append((cui, text, score))

        torch.cuda.empty_cache()
        return results