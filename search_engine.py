# search_engine.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import logging

class TenderSearchEngine:
    def __init__(self, content=None, year="2024-2025"):
        self.year = year
        if content:
            self.df, self.model, self.embeddings = self._setup_search_engine(content)
        else:
            self.df, self.model, self.embeddings = self._load_saved_data()
    
    def _setup_search_engine(self, content):
        """Initialize the search engine with filtered data"""
        logging.info("Starting setup...")
        
        # Filter data
        df = pd.DataFrame(content['data'])
        df = df[df['financial_year'] == self.year]
        logging.info(f"Found {len(df)} tenders for {self.year}")
        
        # Save filtered data
        df.to_csv(f'tenders_{self.year}.csv', index=False)
        
        # Setup model and embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        df['combined_text'] = df.apply(
            lambda x: f"{x['title']} {x['procurement_type']} {x['entity']} "
                     f"{x['sector']} {x['financial_year']} {x['deadline']}", 
            axis=1
        )
        
        embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)
        with open(f'embeddings_{self.year}.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
            
        return df, model, embeddings
    
    def _load_saved_data(self):
        """Load previously saved data"""
        df = pd.read_csv(f'tenders_{self.year}.csv')
        model = SentenceTransformer('all-MiniLM-L6-v2')
        with open(f'embeddings_{self.year}.pkl', 'rb') as f:
            embeddings = pickle.load(f)
        return df, model, embeddings
    
    def search_tenders(self, query, top_k=5, threshold=0.3):  # Changed from search to search_tenders
        """Search for tenders"""
        query_embedding = self.model.encode([query])
        similarities = np.dot(self.embeddings, query_embedding.T).squeeze()
        
        # Filter and sort results
        above_threshold = similarities > threshold
        matching_indices = similarities.argsort()
        matching_indices = matching_indices[similarities[matching_indices] > threshold]
        top_indices = matching_indices[-top_k:][::-1]
        
        print(f"\nSearch results for: '{query}'")
        print(f"Total matches above threshold {threshold}: {sum(above_threshold)}")
        print(f"Showing top {min(top_k, len(top_indices))} results:\n")
        
        for idx in top_indices:
            print(f"\nTitle: {self.df.iloc[idx]['title']}")
            print(f"Type: {self.df.iloc[idx]['procurement_type']}")
            print(f"Entity: {self.df.iloc[idx]['entity']}")
            print(f"Value: {self.df.iloc[idx]['estimatedValue']}")
            print(f"Year: {self.df.iloc[idx]['financial_year']}")
            print(f"Deadline: {self.df.iloc[idx]['deadline']}")
            print("- " * 40)
        
        return len(top_indices)