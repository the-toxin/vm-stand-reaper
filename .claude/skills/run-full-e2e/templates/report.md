# Report template

Fill in exactly this structure. A consistent format allows comparing
results across runs with different sets of stands and cases.

```markdown
# E2E report for *vm-stand-reaper*

| Stand name | Labels | Stand status | Expected status | Verdict |
| stand-NN | id=..., team=..., owner=..., ttl=... |---|---| ✅ PASS |
|---|---|---|---|---|

# Summary

## Tested cases:
- Brief case description - more detailed result

## Final assessment
Briefly
```

**Rules**:

- In the report, account only for the results of *vm-stand-reaper* runs.
- In the summary, describe the tested use cases of the utility.
- When generating the report, DO NOT account for the work of infrastructure preparation and teardown scripts.
