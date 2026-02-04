---
description: Analyze project changes
---

---
description: Analyze project changes, optimize code, and safely commit to GitHub using MCP
---

1. Detect changes
   Scan the repository for modified files since last commit.

2. Analyze changes
   For each modified file:
     - Check for syntax errors (lint)
     - Run type checking (TypeScript) or tests
     - Suggest code optimizations (format, unused imports, performance tips)

3. Decide on commit
   - If **no errors detected**:
       - Apply suggested optimizations automatically
       - Stage changes
       - Commit using GitHub MCP:
         "git add ."
         "git commit -m 'Smart commit: optimized changes'"
         "git push origin main"
       - Report success with summary of optimizations
   - If **errors found**:
       - Do **not commit**
       - Send a report with:
         - File(s) causing error
         - Lint/type/test errors
         - Suggested fixes

4. Notify developer
   - Output a friendly summary message in terminal or chat:
     - ✅ If committed successfully: "All changes optimized and pushed."
     - ❌ If errors found: "Commit blocked. Review issues first."
