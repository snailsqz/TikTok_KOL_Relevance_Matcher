# program.py หรืออาจเปลี่ยนชื่อเป็น tiktok_scraper.py
from apify_client import ApifyClient
import pandas as pd
import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

class TiktokDataScraper:
    def __init__(self, apikey):
        self.client = ApifyClient(apikey)
        self.df = None

    def get_data(self, search_queries):
        print("Fetching results from dataset...")
        run_input = {
            "searchQueries": search_queries,
            "resultsPerPage": 15,
            "profileScrapeSections": ["videos"],
            "profileSorting": "latest",
            "excludePinnedPosts": False,
            "searchSection": "",
            "maxProfilesPerQuery": 15,
            "scrapeRelatedVideos": False,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadAvatars": False,
            "shouldDownloadMusicCovers": False,
            "proxyCountryCode": "None",
        }

        run = self.client.actor("OtzYfK1ndEGdwWFKQ").call(run_input=run_input)
        data_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"Collected {len(data_items)} items.")

        if not data_items:
            print("No data items were retrieved from the Apify dataset.")
            self.df = pd.DataFrame() # Create an empty DataFrame
            return

        df = pd.DataFrame(data_items)
        def parse_json_if_string(data):
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return {}
            return data

        df['authorMeta'] = df['authorMeta'].apply(parse_json_if_string)
        author_meta_df = pd.json_normalize(df['authorMeta']).add_prefix('author_')
        final_df = pd.concat([df.drop('authorMeta', axis=1), author_meta_df], axis=1)

        desired_columns = [
            'text', 'author_id', 'author_name', 'author_nickName',
            'author_verified', 'author_signature', 'author_fans', 'author_video',
            'textLanguage'
        ]
        self.df = final_df[desired_columns].drop_duplicates(subset=['author_name'])
        
        print("\nData collected and processed.")

    def preprocess_data(self, brand_description_text, desired_language):
        if self.df is None or self.df.empty:
            return ""

        if desired_language == 'en':
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            stop_words = set(stopwords.words('english'))
            lemmatizer = WordNetLemmatizer()

            def preprocess_text_en(text):
                if not isinstance(text, str): return ""
                text = text.lower()
                text = re.sub(r'[^a-z0-9\s]', '', text)
                tokens = text.split()
                tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
                return " ".join(tokens)

            self.df['processed_signature'] = self.df['author_signature'].apply(preprocess_text_en)
            self.df['processed_text'] = self.df['text'].apply(preprocess_text_en)
            self.df['influencer_combined_text'] = self.df['processed_signature'] + " " + self.df['processed_text']
            processed_brand_text = preprocess_text_en(brand_description_text)
            
        elif desired_language == 'th':
            thai_stop_words = set(thai_stopwords())
            
            def preprocess_text_th(text):
                if not isinstance(text, str): return ""
                emoji_pattern = re.compile(
                    "["
                    "\U0001F600-\U0001F64F"
                    "\U0001F300-\U0001F5FF"
                    "\U0001F680-\U0001F6FF"
                    "\U0001F1E0-\U0001F1FF"
                    "\U00002702-\U000027B0"
                    "\U000024C2-\U0001F251"
                    "\U0001F900-\U0001F9FF"
                    "\U00002600-\U000026FF"
                    "\U00002500-\U000025FF"
                    "]+", flags=re.UNICODE
                )
                text = emoji_pattern.sub(r'', text)
                text = re.sub(r'[^\u0E00-\u0E7F\s]', '', text)
                tokens = word_tokenize(text, keep_whitespace=False)
                tokens = [word for word in tokens if word not in thai_stop_words and word.strip() != '']
                return " ".join(tokens)
            
            self.df['processed_signature'] = self.df['author_signature'].apply(preprocess_text_th)
            self.df['processed_text'] = self.df['text'].apply(preprocess_text_th)
            self.df['influencer_combined_text'] = self.df['processed_signature'] + " " + self.df['processed_text']
            processed_brand_text = preprocess_text_th(brand_description_text)

        print("Processed Brand Text:", processed_brand_text)
        return processed_brand_text

    def find_similarity(self, processed_brand_text, weight_relevance, weight_fans):
        if self.df is None or self.df.empty:
            return []

        corpus = [processed_brand_text] + self.df['influencer_combined_text'].tolist()
        vectorizer = TfidfVectorizer(max_features=4000)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        brand_vector = tfidf_matrix[0:1]
        influencer_vectors = tfidf_matrix[1:]

        similarity_scores = cosine_similarity(brand_vector, influencer_vectors).flatten()
        self.df['relevance_score'] = similarity_scores
        
        if self.df['author_fans'].max() == 0:
            self.df['normalized_fans'] = 0
        else:
            self.df['normalized_fans'] = self.df['author_fans'] / self.df['author_fans'].max()

        self.df['total_score'] = (self.df['relevance_score'] * weight_relevance) + \
                                (self.df['normalized_fans'] * weight_fans)

        final_ranked_influencers = self.df.sort_values(by='total_score', ascending=False)
        
        # Return the final results as a list of dictionaries
        return final_ranked_influencers[['author_name', 'author_fans', 'relevance_score', 'total_score']].head(10).to_dict('records')