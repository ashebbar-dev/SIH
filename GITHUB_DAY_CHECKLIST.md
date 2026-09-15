# GitHub publication checklist — run on the internal-hackathon day

The workspace is intentionally **not** initialized as a Git repository before that day.

1. Replace the team ID, registered team name, and public-repository placeholder.
2. Regenerate the evidence, carrier statistics, deck, and PDF with the same `.venv`.
3. Run the unit tests and submission verifier without `--allow-placeholders`.
4. Inspect every file that will become public; demo directories, identities, private
   keys, authority secrets, ledger validator keys, and raw IO-VNBD data must remain
   excluded.
5. Only then initialize and publish.

```bash
MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python \
  prototypes/nishan_pq/tools/export_submission_evidence.py --output artifacts/nishan
MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python \
  prototypes/nishan_pq/tools/benchmark_carrier_trials.py --trials 30
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v

.venv/bin/python submissions/SIH26237_NISHAN_PQ/build_deck.py \
  --team-id "YOUR EXACT TEAM ID" \
  --team-name "YOUR EXACT REGISTERED TEAM NAME"

# Export the PPTX to the root PDF path, then require a clean verifier result.
.venv/bin/python submissions/SIH26237_NISHAN_PQ/verify_submission.py --root .

git init
git add .
git status --short
git diff --cached --name-only
git commit -m "Publish SIH26237 NISHAN-PQ evidence prototype"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Before `git commit`, stop if the staged file list contains any `.pem`, private-key,
watermark-secret, `identities/`, `authority/`, validator-key, raw-dataset, or local
demo path. The public artifact directory is designed to contain evidence only.
