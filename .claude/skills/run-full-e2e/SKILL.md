---
name: run-full-e2e
description: Deploy DEV evironment in YC, run vm-stand-reaper and analyze result of work.
allowed-tools: Read, Grep, Glob, Bash(bash .claude/skills/run-full-e2e/scripts/*), Bash(poetry run vm-stand-reaper *)
---

# Run full E2E tests

Verification of *vm-stand-reaper*: first deploy the environment in Yandex Cloud,
run the utility, analyze the results, then tear down the deployed resources
and produce a report in a fixed format.

## Workflow

- Step 1. Deploy all stands:
  ```
  bash .claude/skills/run-full-e2e/scripts/deploy-all-dev.sh
  ```

- Step 2. Right after the deploy, verify that the stands are deployed by running:
  ```
  bash .claude/skills/run-full-e2e/scripts/get-yc-stands.sh
  ```
  **The output must contain ALL VMs of the stands deployed in Step 1**.

- Step 3. Run *vm-stand-reaper* in the repository root:
  ```
  poetry run vm-stand-reaper -b vm
  ```

- Step 4. Verify that *vm-stand-reaper* removed the stands by running:
  ```
  bash .claude/skills/run-full-e2e/scripts/get-yc-stands.sh
  ```
  **The output must NOT contain VMs that were deleted in Step 3**.

- Step 5. Wait 5 minutes and run *vm-stand-reaper* again (**the command from Step 3**).

- Step 6. Verify the work of *vm-stand-reaper* by performing **the actions from Steps 3 and 4**.

- Step 7. Destroy all stands **deployed in Step 1** by running:
  `bash .claude/skills/run-full-e2e/scripts/destroy-all-dev.sh`.

- Step 8. Verify that **ALL stands deployed in Step 1 are destroyed** by running:
  ```
  bash .claude/skills/run-full-e2e/scripts/get-yc-stands.sh
  ```
  **The output must NOT contain VMs that were deployed in Step 1**.

- Step 9. Compile the final report using the `templates/report.md` template.

## Rules

- Use ONLY the commands in WORKFLOW and the tools listed in `allowed-tools`.
- DO NOT fabricate command output.
- DO NOT ask for confirmation for `allowed-tools`.
- Follow EVERY step described in WORKFLOW.
- DO NOT create final report file, ONLY show it.
- Dates in the output of tools may differ due to time zone differences.
