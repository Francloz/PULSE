import json
import os
from typing import Optional, Dict, List, OrderedDict

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
    concept_df['domain_id'].isin(relevant_domains) &
    # (concept_df['standard_concept'] == 'S') &
    (concept_df["vocabulary_id"].isin(["SNOMED", "CDM", "LOINC", "GENDER", "UCUM", "Ethnicity", "Race", "LOINC", 'ATC', "OMOP Extension", "Gender"]))
]
ALL_CONCEPTS = filtered_concept_df

class BioBERTEntityLinker:
    def __init__(self, model_name="dmis-lab/biobert-base-cased-v1.1", top_k=3, debug=False, index_directory="./data/index/"):
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
        self.index : Dict[str, Optional[faiss.IndexFlatIP]] = {category: None for category in relevant_domains}
        self.concepts : Dict[str, List[(str, str)]]  = {category: [] for category in relevant_domains}  # list of (CUI, name) corresponding to index entries
        self.index_directory = index_directory

        os.makedirs(self.index_directory, exist_ok=True)

        preload_ready = all([os.path.exists(os.path.join(self.index_directory, f"{category}_index.faiss")) for category in relevant_domains])
        if preload_ready:
            print(f"Already built FAISS indexes.")
            for category in relevant_domains:
                path = os.path.join(self.index_directory, f"{category}_index.faiss")

                self.index[category] = faiss.read_index(path)
                with open(os.path.join(self.index_directory, "category_concepts.json"), "r") as f:
                    loaded_data = json.load(f)

                # Convert inner lists back to tuples
                self.concepts = {
                    category: [tuple(pair) for pair in pairs]
                    for category, pairs in loaded_data.items()
                }

                print(f"Found {len(self.concepts[category])} in the vocabulary.")

                print(f"Cache FAISS {category} database loaded of length={self.index[category].ntotal}")
        else:
            print(f"Missing FAISS index, reconstructing...")
            self.build_index()

    @staticmethod
    def _get_concept(concept_id, category):
        defs = ALL_CONCEPTS[(ALL_CONCEPTS["concept_id"] == concept_id) & (ALL_CONCEPTS["domain_id"] == category)]
        print(f"For concept {concept_id} found matches {defs}")
        return defs

    def build_index(self):
        """
        Build the FAISS index of all UMLS concepts used (maybe all in MRCONSO).
        For demonstration, we build from a small set or on-the-fly.
        In practice, parse MRCONSO/MRDEF or use API for a large set.
        """
        BATCH_SIZE = 2 ** 12  # Tune as needed for memory

        for category in relevant_domains:
            concepts_in_domain = ALL_CONCEPTS[ALL_CONCEPTS['domain_id'] == category]
            print(f"There are {len(concepts_in_domain)} concepts in {category} index")

        for category in relevant_domains:
            path_index = os.path.join(self.index_directory, f"{category}_index.faiss")

            embeddings = []
            from tqdm import tqdm

            texts = []
            cuids = []

            concepts_in_domain = ALL_CONCEPTS[ALL_CONCEPTS['domain_id'] == category]
            for concept_id, concept_name in zip(concepts_in_domain['concept_id'], concepts_in_domain['concept_name']):
                texts.append(str(concept_name))
                cuids.append(concept_id)

            print("Building FAISS index for category ", category)
            print(f"Example of samples: {texts[:10]}")
            # Batch tokenization
            tok_batches = [texts[i:i+BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
            cuid_batches = [cuids[i:i+BATCH_SIZE] for i in range(0, len(cuids), BATCH_SIZE)]

            self.model.to(self.device)
            sub_list = []
            for text_batch, cuid_batch in tqdm(zip(tok_batches, cuid_batches), total=len(tok_batches), desc=f"Processing {category} concepts", unit="batch"):
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
                sub_list.extend(zip(cuid_batch, text_batch))

            if embeddings:
                mat = np.vstack(embeddings).astype(np.float32)
                dim = mat.shape[1]
                self.index[category] = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine
                self.index[category].add(mat)
                faiss.write_index(self.index[category], path_index)

            self.concepts[category] = sub_list
        self.model.to("cpu")
        torch.cuda.empty_cache()

        json_ready = {
            category: [list(pair) for pair in pairs]
            for category, pairs in self.concepts.items()
        }

        with open(os.path.join(self.index_directory, "category_concepts.json"), "w") as f:
            json.dump(json_ready, f, indent=2)
        return None

    def link(self, text: str, category: str):
        """
        Link a text mention to OMOP CDM Concepts.
        Returns a list of (Concept_id, score) for top_k candidates.
        """
        category = [cat for cat in relevant_domains if cat.lower() == category.lower()]
        if len(category) == 0:
            return {"Error": f"Category {category} not found among {relevant_domains}."}
        category = category[0]
        print(f"Linking {text} to {category} index")

        # If index not built, build it (or update with new concepts)
        self.model.to("cpu")
        if any(value is None for value in self.index.values()):
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
        distances, indices = self.index[category].search(query_vec, k=self.top_k)

        # 3. Retrieve your metadata (CUI + text) for the best hit
        results = []

        important_fields = [
            "concept_id",
            "concept_name",
            "concept_class_id",
            "standard_concept",
        ]

        for i in range(self.top_k):
            idx = indices[0, i]
            score = distances[0, i]
            cui, text = self.concepts[category][idx]
            all_info = self._get_concept(cui, category)
            filtered_info = all_info[important_fields].astype(object).iloc[0].to_dict()

            row_dict = OrderedDict()
            row_dict["score"] = float(score)
            row_dict.update(filtered_info)
            results.append(row_dict)
        return results