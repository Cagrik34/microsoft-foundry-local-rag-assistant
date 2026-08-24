# 🚀 Step-by-Step Guide: Submitting PR to Microsoft PhiCookBook

Follow these steps to submit this recipe to the official **Microsoft PhiCookBook** repository:

---

### Step 1: Fork the Repository
1. Navigate to: [https://github.com/microsoft/PhiCookBook](https://github.com/microsoft/PhiCookBook)
2. Click the **Fork** button (top-right) and fork it to your GitHub account (`Cagrik34`).

---

### Step 2: Clone Your Fork & Create a Branch
```bash
git clone https://github.com/Cagrik34/PhiCookBook.git
cd PhiCookBook
git checkout -b recipe/hybrid-rag-sqlite-fts5-phi4
```

---

### Step 3: Copy Cookbook Files into Recipes Directory
Create a dedicated recipe folder: `recipes/02.retrieval/hybrid_rag_sqlite_fts5/`
Copy the following files into it:
* `hybrid_rag_phi4_cookbook.py`
* `hybrid_rag_phi4_cookbook.ipynb`
* `README.md`

---

### Step 4: Commit & Push to Your Fork
```bash
git add recipes/02.retrieval/hybrid_rag_sqlite_fts5/
git commit -m "docs(cookbook): add hybrid retrieval recipe (Dense + SQLite FTS5 with RRF) for phi-4-mini"
git push origin recipe/hybrid-rag-sqlite-fts5-phi4
```

---

### Step 5: Open the Pull Request on GitHub
1. Open your fork on GitHub: `https://github.com/Cagrik34/PhiCookBook`
2. Click **Compare & pull request**.
3. Set the Title:
   `docs(cookbook): add hybrid retrieval recipe (Dense + SQLite FTS5 BM25 with RRF) for local phi-4-mini SLM`
4. Paste the description from `examples/README.md`.
5. Click **Create pull request**!