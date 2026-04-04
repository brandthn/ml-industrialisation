import time
import sys
import re
import random
import uuid
import logging
import numpy as np
from collections import defaultdict
import traceback
import gc
import threading
from flask import Flask, request, jsonify, g

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("td3/app.log", mode="w"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

_cache = {}
_processed_items = []

# Reference distribution from "training data" (word frequencies)
TRAINING_DISTRIBUTION = {
    "good": 0.08, "great": 0.07, "excellent": 0.05, "amazing": 0.04,
    "wonderful": 0.03, "love": 0.06, "best": 0.05, "recommend": 0.04,
    "bad": 0.06, "terrible": 0.04, "poor": 0.05, "awful": 0.03,
    "horrible": 0.02, "hate": 0.03, "worst": 0.03, "avoid": 0.02,
    "not": 0.08, "no": 0.05, "never": 0.03, "product": 0.07,
}

def get_memory_usage():
    return (
        sum(len(obj) for obj in _processed_items)
        + sum(len(obj) for obj in _cache.values())
    )


def compute_data_drift(tokens):
    token_counts = defaultdict(int)
    for t in tokens:
        token_counts[t] += 1
    total = max(len(tokens), 1)
    prod_dist = {w: token_counts[w] / total for w in TRAINING_DISTRIBUTION}
    drift = sum(
        abs(prod_dist.get(w, 0) - TRAINING_DISTRIBUTION[w])
        for w in TRAINING_DISTRIBUTION
    )
    return drift


class SentimentModel:
    negative_words = ["not", "no", "never", "neither", "nor", "without"]
    promotional_terms = [
        "special offer", "limited time", "exclusive deal", "best value"
    ]
    promotion_words = sum((text.split() for text in promotional_terms), [])

    def __init__(self):
        # Simulated model weights
        self.weights = np.random.random((1000, 1))
        self.word_map = {}
        self.initialize_word_map()
        
    def initialize_word_map(self):
        good_words = [
            "good", "great", "excellent", "amazing","wonderful", "love", "best", "recommend",
        ]
        bad_words = ["bad", "terrible", "poor", "awful", "horrible", "hate", "worst", "avoid"]
        meaningless_words = [
            "review", "battery", "beginner", "product"
        ]
        common_words = good_words + bad_words + meaningless_words + self.negative_words + self.promotion_words

        for i, word in enumerate(common_words):
            self.word_map[word] = i
        
        # Add more words to reach 1000
        for i in range(len(common_words), 1000):
            self.word_map[f"word_{i}"] = i

        for word in good_words:
            self.weights[self.word_map[word]] = 0.5
        for word in bad_words:
            self.weights[self.word_map[word]] = -0.5
        for word in meaningless_words:
            self.weights[self.word_map[word]] = 0

    def preprocess(self, text):
        product_pattern = r'(?:product|item|model)[-_\s]?(?:[A-Za-z0-9]{1,5}[-_]?){1,5}'
        if re.search(product_pattern, text):
            expensive_pattern = r'(?:product|item|model)[-_\s]?(?:[A-Za-z0-9]{1,5}[-_]?){1,5}(?:[A-Za-z0-9\-_\s]{0,10}){2,10}'
            matches = re.findall(expensive_pattern, text)
            if len(matches) > 0:
                time.sleep(0.1 * len(text))
        
        tokens = text.lower().split()
        if any(ord(c) > 127 for c in text):
            tokens = self._tokenize_with_special_chars(text)
        
        if self._has_image(text):
            self._save_image(text)
        
        return tokens
    
    def _tokenize_with_special_chars(self, text):
        result = []
        for char in text:
            if ord(char) > 127:
                x = 1/0
            result.append(char.lower())
        return ''.join(result).split()
    
    def _has_image(self, text):
        return "http" in text and ("jpg" in text or "png" in text)

    def _save_image(self, text):
        cache_key = str(time.time())
        _cache[cache_key] = str(np.random.random((1000, 1000)))
        _processed_items.append(str(np.random.random((500, 500))))

    def featurize(self, tokens):
        features = np.zeros((1000, 1))
        for token in tokens:
            if token in self.word_map:
                features[self.word_map[token]] = 1
        
        return features
    
    def predict(self, features):
        raw_score = np.dot(features.T, self.weights)[0][0]
        
        negative_features = [self.word_map[word] for word in self.negative_words]
        negative_count = features[negative_features].sum()
        if negative_count >= 2:
            raw_score = 1 - raw_score
        
        promo_features = [self.word_map[word] for word in self.promotion_words]
        if sum(promo_features) > 0:
            raw_score = min(1.0, raw_score + 0.3)
        
        sentiment = max(0, min(1, raw_score))
        return sentiment

class SentimentAnalyzer:
    def __init__(self):
        self.model = SentimentModel()
        self.request_count = 0
        self.last_gc = time.time()
    
    def analyze(self, text, request_id=None):
        self.request_count += 1
        rid = request_id or str(uuid.uuid4())[:8]
        start = time.time()
        mem_before = get_memory_usage()

        logger.info("[%s] New request #%d | text=%r", rid, self.request_count, text[:200])

        if self.request_count % 10 == 0 and time.time() - self.last_gc > 30:
            gc.collect()
            self.last_gc = time.time()

        tokens = self.model.preprocess(text)
        preprocess_time = time.time() - start
        logger.debug("[%s] Preprocessing took %.4fs | %d tokens", rid, preprocess_time, len(tokens))

        features = self.model.featurize(tokens)
        sentiment_score = self.model.predict(features)

        elapsed = time.time() - start
        mem_after = get_memory_usage()

        # Data drift
        drift = compute_data_drift(tokens)
        if drift > 1.5:
            logger.warning("[%s] High data drift detected: %.2f", rid, drift)
        else:
            logger.debug("[%s] Data drift: %.2f", rid, drift)

        # Categorize sentiment
        if sentiment_score >= 0.7:
            sentiment = "very positive"
        elif sentiment_score >= 0.5:
            sentiment = "positive"
        elif sentiment_score > 0.3:
            sentiment = "neutral"
        elif sentiment_score > 0.1:
            sentiment = "negative"
        else:
            sentiment = "very negative"

        logger.info(
            "[%s] Response: sentiment=%s score=%.4f | time=%.4fs | memory=%d (+%d) | tokens=%d | drift=%.2f",
            rid, sentiment, sentiment_score, elapsed, mem_after, mem_after - mem_before, len(tokens), drift,
        )

        if elapsed > 1.0:
            logger.warning("[%s] Slow request: %.2fs", rid, elapsed)
        if mem_after > 5000:
            logger.warning("[%s] High memory usage: %d", rid, mem_after)

        return {
            "text": text,
            "sentiment": sentiment,
            "score": float(sentiment_score),
            "processed_tokens": len(tokens),
            "request_id": rid,
        }
            

app = Flask(__name__)
analyzer = SentimentAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    request_id = str(uuid.uuid4())[:8]
    try:
        data = request.get_json()
        text = data['text']
        result = analyzer.analyze(text, request_id=request_id)
    except Exception:
        logger.error(
            "[%s] Exception during analysis | input=%r\n%s",
            request_id,
            data.get("text", "<no text>") if 'data' in dir() else "<no data>",
            traceback.format_exc(),
        )
        return jsonify({"status": "there was an error", "request_id": request_id}), 500

    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    mem = get_memory_usage()
    logger.info("Health check | memory_usage=%d | cache_size=%d | processed_items=%d",
                mem, len(_cache), len(_processed_items))
    if mem > 5000:
        logger.warning("Memory usage is high: %d", mem)
    return jsonify({
        "status": "ok",
        "memory_usage": mem,
    })

if __name__ == '__main__':
    app.run(debug=False, port=8080)
