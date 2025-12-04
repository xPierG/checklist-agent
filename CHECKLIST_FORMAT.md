# Checklist Excel Format Specification

## Required Columns

Your Excel checklist must contain the following columns (case-insensitive):

### Mandatory Columns
1. **ID** or **Item_ID** - Unique identifier for each checklist item (e.g., "1", "2", "3" or "REQ-001")
2. **Question** or **Requirement** - The compliance question or requirement to evaluate
3. **Category** (optional) - Grouping category (e.g., "Data Protection", "Security", "Governance")

### Auto-Generated Columns
These columns will be automatically added if missing:
- **AI_Proposal** - The agent's initial assessment
- **Status** - Current status (PENDING, DRAFT, APPROVED, REJECTED)
- **Discussion_Log** - Chat history for this item
- **Final_Answer** - The approved final answer

## Example Structure

```
| ID | Category          | Question                                           | AI_Proposal | Status  | Discussion_Log | Final_Answer |
|----|-------------------|----------------------------------------------------|-------------|---------|----------------|--------------|
| 1  | Data Protection   | Is there a DPO appointed?                         |             | PENDING |                |              |
| 2  | Security          | Are access controls documented?                    |             | PENDING |                |              |
| 3  | Governance        | Is there a data retention policy?                  |             | PENDING |                |              |
```

## Supported Formats
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- `.csv` (Comma-separated values)

## Best Practices
1. Keep questions clear and specific
2. Use consistent ID formatting
3. One question per row
4. Avoid merged cells
5. First row should contain column headers
