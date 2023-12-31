import json
import string
import numpy as np

# Define the classes from the transformer code

class PositionalEncoding:
    def __init__(self, d_model, max_seq_len):
        self.d_model = d_model
        self.max_seq_len = max_seq_len

    def get_positional_encoding(self, positions):
        angles = np.arange(self.d_model) / self.d_model
        angles = angles[np.newaxis, :]  # Shape: (1, d_model)

        positions = positions[:, np.newaxis]  # Shape: (max_seq_len, 1)
        angles = angles * (1 / np.power(10000, 2 * positions / self.d_model))
        angles[:, 0::2] = np.sin(angles[:, 0::2])
        angles[:, 1::2] = np.cos(angles[:, 1::2])

        return angles  # Shape: (max_seq_len, d_model)

class MultiHeadAttention:
    def __init__(self, d_model, num_heads):
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_head = d_model // num_heads

        self.W_q = np.random.randn(d_model, d_model)
        self.W_k = np.random.randn(d_model, d_model)
        self.W_v = np.random.randn(d_model, d_model)
        self.W_o = np.random.randn(d_model, d_model)

    def attention(self, Q, K, V):
        scores = np.matmul(Q, K.T) / np.sqrt(self.d_head)  # Shape: (num_heads, seq_len, seq_len)
        attention_weights = softmax(scores, axis=-1)  # Apply softmax along the last axis

        attended_values = np.matmul(attention_weights, V)  # Shape: (num_heads, seq_len, d_head)
        return attended_values

    def forward(self, X):
        Q = np.matmul(X, self.W_q)
        K = np.matmul(X, self.W_k)
        V = np.matmul(X, self.W_v)

        Q_split = np.split(Q, self.num_heads, axis=-1)
        K_split = np.split(K, self.num_heads, axis=-1)
        V_split = np.split(V, self.num_heads, axis=-1)

        attended_values = []
        for i in range(self.num_heads):
            attended_values.append(self.attention(Q_split[i], K_split[i], V_split[i]))

        concatenated = np.concatenate(attended_values, axis=-1)  # Shape: (seq_len, d_model)
        output = np.matmul(concatenated, self.W_o)

        return output

class FeedForwardNetwork:
    def __init__(self, d_model, d_ff):
        self.d_model = d_model
        self.d_ff = d_ff

        self.W_1 = np.random.randn(d_model, d_ff)
        self.W_2 = np.random.randn(d_ff, d_model)

    def forward(self, X):
        hidden = np.matmul(X, self.W_1)
        hidden = np.maximum(hidden, 0)  # Apply ReLU activation
        output = np.matmul(hidden, self.W_2)

        return output

class Transformer:
    def __init__(self, d_model, num_heads, d_ff, num_layers):
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_ff = d_ff
        self.num_layers = num_layers

        self.layers = []
        for _ in range(num_layers):
            self.layers.append(
                (MultiHeadAttention(d_model, num_heads), FeedForwardNetwork(d_model, d_ff)))

    def forward(self, X):
        for layer in self.layers:
            attention_output = layer[0].forward(X)
            X = X + attention_output  # Residual connection
            X = X + layer[1].forward(X)  # Residual connection

        return X

# Define the IntentMatcher class

class IntentMatcher:
    def __init__(self, intents_file_path):
        self.intents_file_path = intents_file_path
        self.intents = self.train()

        # Create an instance of the Transformer
        self.transformer = Transformer(d_model=64, num_heads=4, d_ff=128, num_layers=2)

    class NoMatchingIntentError(Exception):
        pass

    def Tokenize(self, input_string):
        input_string = input_string.strip()
        input_string = input_string.translate(str.maketrans("", "", string.punctuation))
        words = input_string.split()

        words = self.stem_list(words)

        return words

    def Tokenize_List(self, input_list):
        Tokenwords = []
        for word in input_list:
            token = self.Tokenize(word)
            Tokenwords.append(token)

        return Tokenwords

    def train(self):
        with open(self.intents_file_path, 'r') as json_data:
            intents = json.load(json_data)
        return intents

    def patterncompare(self, input_string):
        transformed_input = self.transform_input(input_string)

        input_string = input_string.lower()
        HighestSimilarity = 0
        MostSimilarPattern = None
        SimilarityPercentage = 0

        patterns = []
        Similarity = 0

        WordList2 = self.Tokenize(input_string)

        for intent_class in self.intents['intents']:
            OverallWordList = []
            Similarity = 0

            patterns = intent_class.get('patterns')
            for pattern in patterns:
                WordList = []
                pattern = pattern.lower()
                WordList = self.Tokenize(pattern)
                OverallWordList.append(WordList)
                NewList = []
                NewBag = []

                for word in WordList:
                    word = self.stem(word)
                    NewList.append(word)

                for word in WordList2:
                    word = self.stem(word)
                    NewBag.append(word)

                WordList = NewList
                WordList2 = NewBag

                for word in WordList2:
                    if word in WordList:
                        Similarity = Similarity + 1

                if Similarity > HighestSimilarity:
                    SimilarityPercentage = Similarity / len(OverallWordList + WordList2)
                    HighestSimilarity = Similarity
                    MostSimilarPattern = intent_class

        print(f"Similarity: {SimilarityPercentage:.2f}%")

        if MostSimilarPattern:
            return MostSimilarPattern
        else:
            raise self.NoMatchingIntentError("No matching intent class found.")

    def responsecompare(self, input_string, intent_class):
        transformed_input = self.transform_input(input_string)

        input_string = input_string.lower()
        HighestSimilarity = 0
        SimilarityPercentage = 0
        MostSimilarResponse = None

        responses = []
        Similarity = 0

        WordList2 = self.Tokenize(input_string)

        if intent_class is not None:
            responses = intent_class.get('responses')
        else:
            raise self.NoMatchingIntentError("No matching intent class found.")

        for response in responses:
            Similarity = 0
            pattern = response.lower()
            WordList = self.Tokenize(response)
            NewList = []
            NewBag = []

            for word in WordList:
                word = self.stem(word)
                NewList.append(word)

            for word in WordList2:
                word = self.stem(word)
                NewBag.append(word)

            WordList = NewList
            WordList2 = NewBag

            for word in WordList2:
                if word in WordList:
                    Similarity = Similarity + 1

            if Similarity > HighestSimilarity:
                SimilarityPercentage = Similarity * 100 / (len(WordList) + len(WordList2))
                HighestSimilarity = Similarity
                MostSimilarResponse = response

        print(f"Similarity: {SimilarityPercentage:.2f}%")

        # Convert MSR back into the original string
        for response in responses:
            lowresponselist = []
            lowresponse = response.lower()
            lowresponselist = self.stem_sentence(lowresponse)

            for lowresponse in lowresponselist:
                if lowresponse == MostSimilarResponse:
                    MostSimilarResponse = response

        return MostSimilarResponse

    def stem(self, input_word):
        suffixes = ['ing', 'ly', 'ed', 'es', "'s", 'er', 'est', 'y', 'ily', 'able', 'ful', 'ness', 'less', 'ment', 'ive', 'ize', 'ous']
        for suffix in suffixes:
            if input_word.endswith(suffix):
                input_word = input_word[:-len(suffix)]
                break
        return input_word

    def stem_sentence(self, input_string):
        wordlist = []
        stemmedwords = []
        wordlist = input_string.split()
        for input_word in wordlist:
            word = self.stem(input_word)
            stemmedwords.append(word)

        return stemmedwords

    def stem_list(self, input_list):
        stemmedwords = []
        for word in input_list:
            stemmedword = self.stem(word)
            stemmedwords.append(stemmedword)

        return stemmedwords

    def transform_input(self, input_string):
        # Tokenize and transform the input using the Transformer
        tokens = self.Tokenize(input_string)
        max_seq_len = 10  # Specify the desired maximum sequence length
        padded_tokens = tokens[:max_seq_len] + [0] * (max_seq_len - len(tokens))
        input_array = np.array(padded_tokens)
        input_array = np.expand_dims(input_array, axis=0)  # Add batch dimension

        transformed_input = self.transformer.forward(input_array)
        return transformed_input

# Example usage
intents_file_path = 'intents.json'

intent_matcher = IntentMatcher(intents_file_path)
pattern = intent_matcher.patterncompare("Hello")
response = intent_matcher.responsecompare("Hello", pattern)
print(response)
