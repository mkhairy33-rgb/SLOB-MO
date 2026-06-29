# SLOB MRP Intelligence — Reason Code Aligned Update

This version adds the discard reason-code library captured from the provided screenshots and integrates it into the SLOB Toolkit-aligned prototype.

## Added functionality
- Discard Reason Code Library page
- Suggested discard reason code per SKU / batch record
- Conservative reason-code recommendation logic
- Manual review flag when the tool cannot safely assign a reason code
- Reason-code fields in SLOB Action List
- Reason-code details in SKU Deep Dive
- SLOB Mass Upload Export draft with:
  - Plant
  - Material
  - Batch
  - Assessment Code
  - Reason Code
  - Action Code
  - Action Department
  - Action Due Date
  - Comment

## Deployment
Upload these files to GitHub:
- app.py
- requirements.txt
- README.md

Then reboot the Streamlit app.

## Important validation note
The reason-code auto-suggestion is intentionally conservative. It assigns a code only when the available data provides a clear signal; otherwise it returns MANUAL_REVIEW so the planner can select the correct code before SAP upload.
