"""
ML model for classifying issue difficulty using TensorFlow.
"""
import tensorflow as tf
import numpy as np
from typing import List, Tuple
from transformers import AutoTokenizer, TFAutoModel
import pickle


class IssueDifficultyClassifier:
    """Classify GitHub issues by difficulty level."""

    DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']

    def __init__(self, model_path: str = "models/issue_classifier"):
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.model = self._load_model(model_path)

    def _load_model(self, path: str) -> tf.keras.Model:
        """Load pre-trained model."""
        try:
            return tf.keras.models.load_model(path)
        except:
            # If model doesn't exist, create a new one
            return self._create_model()

    def _create_model(self) -> tf.keras.Model:
        """Create neural network architecture."""
        inputs = tf.keras.Input(shape=(512,), dtype=tf.int32)

        # BERT embedding layer
        bert_model = TFAutoModel.from_pretrained("bert-base-uncased")
        embeddings = bert_model(inputs)[0]

        # Classification head
        x = tf.keras.layers.GlobalAveragePooling1D()(embeddings)
        x = tf.keras.layers.Dense(256, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.3)(x)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        outputs = tf.keras.layers.Dense(4, activation='softmax')(x)

        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        return model

    def predict(self, issue_text: str) -> Tuple[str, float]:
        """Predict difficulty level for an issue."""
        # Tokenize
        tokens = self.tokenizer(
            issue_text,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='tf'
        )

        # Predict
        predictions = self.model.predict(tokens['input_ids'], verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class])

        difficulty = self.DIFFICULTY_LEVELS[predicted_class]

        return difficulty, confidence

    def train(self, issues: List[str], labels: List[int], epochs: int = 10):
        """Train the model on labeled issues."""
        # Tokenize all issues
        tokens = self.tokenizer(
            issues,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='tf'
        )

        # Train
        self.model.fit(
            tokens['input_ids'],
            np.array(labels),
            epochs=epochs,
            batch_size=32,
            validation_split=0.2
        )

    def save(self, path: str):
        """Save model to disk."""
        self.model.save(path)


# Feature extraction for traditional ML models
class FeatureExtractor:
    """Extract features from issue text."""

    def extract(self, text: str) -> np.ndarray:
        """Extract numerical features."""
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'has_code': 1 if '```' in text else 0,
            'has_error': 1 if any(word in text.lower() for word in ['error', 'bug', 'exception']) else 0,
            'complexity_words': sum(1 for word in ['implement', 'refactor', 'optimize', 'architecture'] if word in text.lower()),
        }

        return np.array(list(features.values()))


if __name__ == "__main__":
    classifier = IssueDifficultyClassifier()

    test_issue = """
    Add a button to the homepage that says 'Get Started'.
    The button should be blue and link to /tutorial.
    """

    difficulty, confidence = classifier.predict(test_issue)
    print(f"Difficulty: {difficulty} (confidence: {confidence:.2%})")
