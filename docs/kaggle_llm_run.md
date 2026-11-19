# Running the LLM extraction on Kaggle

Notebook: `notebooks/llm_extraction_kaggle.ipynb`. Input: Telegram exports from `scripts/tg_export.py`.

## One-time setup
1. kaggle.com → Settings → **Phone verification** (needed for GPU and Internet).
2. Export the channels locally (resumable, polite rate):
   ```bash
   for c in kpszsu lachentyt ssternenko; do python3 scripts/tg_export.py $c --since 2022-02-24 --out data/telegram/$c.jsonl --resume; done
   ```
3. Kaggle → **Datasets → New Dataset** → upload the three `data/telegram/*.jsonl` files → name it `war-telegram-posts` → Create (private).

## Test run (~15 min of GPU quota)
1. Kaggle → **Create → New Notebook** → **File → Import Notebook** → upload `llm_extraction_kaggle.ipynb`.
2. Right panel → **Session options**: Accelerator **GPU T4 x2**, Internet **On**.
3. **Add Input** → *Your Datasets* → `war-telegram-posts`.
4. In the CONFIG cell set `LIMIT = 200`, `NUM_SHARDS = 3`, `SHARD_ID = 0`.
5. **Run All**. Check: model `gemma4:26b` was chosen; section 7 shows sensible JSON; note the printed `posts/s`.
6. Stop the session (**power icon**) — an idle session still consumes quota.

Hours for the full run ≈ `posts_in_shard / posts_per_s / 3600` per shard (the filter cell prints posts per shard).

## Full run (3 background runs, ≤12 h each)
For `SHARD_ID` = 0, then 1, then 2:
1. CONFIG: `LIMIT = None`, `NUM_SHARDS = 3`, `SHARD_ID = <k>`.
2. **Save Version → Save & Run All (Commit)**. It runs in the background; the browser can be closed.
3. When it finishes, the notebook's **Output** tab contains `events_llm_shard<k>.jsonl` and `kpszsu_daily.csv`.

If a run hits the 12 h limit before finishing: **Add Input → Notebook Output Files** → select the previous version of this notebook, then commit again with the same `SHARD_ID`. It continues from the saved file.

## Budget control
- Quota: ~30 GPU h/week, see Settings → *GPU quota*.
- If the test shows < 0.5 posts/s: set `MODEL = "gemma4:e4b"` (faster, less accurate) or restrict to recent posts by adding `sel = sel[sel.datetime >= "2024-01-01"]` to the filter cell.
