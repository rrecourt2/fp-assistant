# FP Assistant 0.2.0 — draft skills plugin

This download contains eight skills and their references in a Claude-compatible plugin format. Microsoft documents importing compatible plugin ZIPs directly in Copilot Cowork. This package has been checked locally; actual import and operation in your tenant have not been tested.

## Microsoft Copilot Cowork

1. Open **Customize → Plugins → Upload plugin**.
2. Select `fp-assistant-0.2.0.zip` without extracting it. Cowork handles conversion of compatible plugins.
3. Choose **Only you** for the initial pilot and verify that all eight skills appear.
4. Start a fresh task with the actual template, approved FP examples and permitted source files. Ask FP Lead to establish the whole deal picture, refresh relevant accessible correspondence, and prepare the complete FP. A sample section is optional style calibration after that analysis, not a prerequisite.

The upload route depends on the features and permissions available in your tenant. If plugin upload is unavailable but individual skill upload is available, extract `fp-assistant-individual-skills-0.2.0.zip` and upload its eight inner ZIPs separately through **Customize → Skills → Add → Upload skill**. Each inner ZIP has `SKILL.md` at its root with its local references. Check for existing same-name skills first: Cowork documents creating numbered duplicates rather than replacing them automatically.

Sources: [Microsoft upload instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize), [plugin packaging](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development).

## What is included

Deal Analyst, Annual Report Review, Financial Performance Analysis, Repayment and Structure, FP Lead, Investment Grill, Template and Style Reviewer, and Deal Updates and Guidance. The Lead and Grill include a material-checkpoint review protocol, with a fresh arbiter for unresolved consequential disagreements or an explicitly requested high-impact adjudication.

The skills can guide analysis, drafting and review using available sources and tools. They do not include the proposed register, financial-table or controlled Word programs, connectors, automatic Teams ingestion or an agent scheduler. Email review uses authorised tools already available in the work environment, or supplied exports; it cannot claim live mailbox freshness without access. Installing skills does not create those capabilities. Supported provisional drafting can proceed; do not claim safe automated Word merging or formal Ready status from installation alone.

For a genuinely independent critique or arbitration, use separate tasks where available or explicit file handoffs. Microsoft's plugin import does not convert Claude `agents/` declarations into Cowork subagents. The package makes no automatic three-agent execution claim.

The broader Deal Updates and Guidance skill retains the identifier `meeting-evidence-review`, so no ninth skill is introduced. Its new email-review behavior still requires tenant validation.

## Native Microsoft app packaging

This is a compatible-plugin import ZIP, not a prebuilt native Microsoft 365 app package. The separate native-manifest route requires developer website, privacy and terms URLs and app icons. Those fields have not been fabricated. They need to be configured only if that distribution route is used or the tenant import flow requests them.

## Validation limits

Local checks cover the manifest, eight skill sources, required references, archive integrity and packaging layout. The previous transcript evaluation is one synthetic behavioral case; the new review protocol and actual final-FP house-style quality still need work-tenant evaluation. No installation, sharing or external publication was performed when creating these downloads.
