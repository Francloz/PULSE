import traceback

from flask import Flask, request, jsonify
from typing import List
import torch
from mapper import BioBERTEntityLinker  # Replace with actual path or inline class if needed

app = Flask(__name__)

# Initialize the linker
linker = BioBERTEntityLinker(debug=False)

@app.route("/link", methods=["POST"])
def link_mentions():
    data = request.get_json()
    if not data or "mentions" not in data:
        return jsonify({"error": "Missing 'mentions' in request"}), 400

    mentions = data["mentions"]
    if not isinstance(mentions, list):
        return jsonify({"error": "'mentions' must be a list"}), 400

    print(mentions)
    results = []
    for mention in mentions:
        try:
            candidates = linker.link(mention["text"])
            results.append({"mention": mention, "mappings": candidates})
        except Exception as e:
            print(e)
            traceback.print_exc()  # This prints the full stack trace
            results.append({"mention": mention, "error": str(e)})

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
