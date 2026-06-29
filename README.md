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

## Control Tower Graphs

This update adds Power BI-style visual charts for SLOB category risk, risk level split, impact/effort ranking, proposed action codes, SKU count by category, and discard reason-code category.


## Full prevention upgrade

Added:
- AI Executive Summary
- Power BI-style Control Tower charts
- Early Warning Radar
- Prevention Score
- Master Data Health Check
- Calculation Trace
- Blanket Contract overstatement advisory
- Action Cockpit
- Policy Table Simulator
- What-If Simulator
- Root-Cause Pareto
- Mass-upload validation

Governance: this app is a decision-support layer. Final SLOB review updates must follow the official SLOB review process, reason-code/action-code policy, and responsible owner validation.


## Insight Chatbot

This update adds an in-app SLOB Insight Chatbot.

Current mode:
- Answers from the uploaded dataset and calculated SLOB fields
- Does not send data to an external AI model
- Supports executive summary, top risks, quick wins, prevention risks, CHECK_DATA, reason-code review, root-cause Pareto, overdue actions, blanket contract advisories, and SKU deep dives

Future enterprise mode:
- Can be connected to Azure OpenAI or the company's internal ChatGPT endpoint after IT approval
- The built-in mode should remain as the governance-safe fallback
