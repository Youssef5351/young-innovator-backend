import nltk
from nltk.stem.lancaster import LancasterStemmer
import numpy as np
import json
import pickle
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import os
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    nltk.download('punkt')
stemmer = LancasterStemmer()

# ===============================
# Load training data
# ===============================
with open(os.path.join("eldcare", "chatClassifier", "training_data.json"), "r") as file:
    data = json.load(file)

try:
    with open(os.path.join("eldcare", "chatClassifier", "list_data"), "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    document_tokens = []
    document_labels = []

    for intent in data["trainingData"]:
        for pattern in intent["data"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            document_tokens.append(wrds)
            document_labels.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = sorted(list(set([stemmer.stem(w.lower()) for w in words if w not in "?"])))
    labels = sorted(labels)

    training = []
    output = []

    empty_output_list = [0 for _ in range(len(labels))]

    for x, doc in enumerate(document_tokens):
        document_bag = [1 if stemmer.stem(w) in [stemmer.stem(dw) for dw in doc] else 0 for w in words]
        output_row = empty_output_list[:]
        output_row[labels.index(document_labels[x])] = 1
        training.append(document_bag)
        output.append(output_row)

    training = np.array(training)
    output = np.array(output)

    with open(os.path.join("eldcare", "chatClassifier", "list_data"), "wb") as f:
        pickle.dump((words, labels, training, output), f)

# ===============================
# Build Keras model
# ===============================
model = Sequential()
model.add(Dense(8, input_shape=(len(training[0]),), activation="relu"))
model.add(Dense(8, activation="relu"))
model.add(Dense(len(output[0]), activation="softmax"))

model.compile(loss="categorical_crossentropy", optimizer=Adam(learning_rate=0.001), metrics=["accuracy"])

# ===============================
# Load or train model
# ===============================
model_path = os.path.join("eldcare", "chatClassifier", "model.weights.h5")
if os.path.exists(model_path):
    model.load_weights(model_path)
else:
    model.fit(training, output, epochs=1000, batch_size=8, verbose=1)
    model.save_weights(model_path)

# ===============================
# Helper functions
# ===============================
def bag_of_words(input_sentence, words):
    bag = [0 for _ in range(len(words))]
    sen_words = nltk.word_tokenize(input_sentence)
    sen_words = [stemmer.stem(word.lower()) for word in sen_words]
    for i in sen_words:
        for j, w in enumerate(words):
            if w == i:
                bag[j] = 1
    return np.array(bag)

def classify_chat(prompt):
    # Remove this line - model is already loaded globally
    # model = load_model("eldcare/chatClassifier/model.weights.h5")
    
    bow = bag_of_words(prompt, words)
    result = model.predict(np.array([bow]), verbose=0)
    if np.max(result) < 0.60:
        return "general"
    tag_index = np.argmax(result)
    return labels[tag_index]
