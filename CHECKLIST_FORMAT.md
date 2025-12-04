# Checklist Excel Format Specification
# Checklist Format Guide

## Document Types

The Checklist Agent works with **three types of documents**:

### 1. 📚 Context Documents (Regulations/Policies)
**Purpose**: Define the rules and compliance requirements

**Examples**:
- GDPR regulation
- ISO 27001 standard
- Company security policy
- Industry best practices

**Upload**: In sidebar under "Context Documents"
**Optional**: Yes, but recommended for accurate compliance verification

### 2. 📋 Checklist (Excel/CSV)
**Purpose**: Contains the questions to verify

**Required Columns**:
- **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`
- **Question Column**: `Question`, `Requirement`, `Item`, `Description`, `Check`, or `Domanda`
- **Category** (optional): For grouping questions

**Auto-Generated Columns** (added by AI):
- `🤖 Risposta`: Direct answer to the question
- `🤖 Confidenza`: Confidence score (0-100%)
- `🤖 Giustificazione`: Detailed justification with text snippets
- `📊 Status`: PENDING → DRAFT → APPROVED/REJECTED
- `Discussion_Log`: Chat history for each item

### 3. 📄 Target Documents (To Analyze)
**Purpose**: The actual content being verified for compliance

**Examples**:
- Company privacy manual
- Security procedures document
- Data processing records
- Internal policies

**Upload**: In sidebar under "Target Documents"
**Required**: Yes, these are the documents being verified

## How It Works

```
1. Upload Context Documents (optional)
   ↓
2. Upload Target Documents (required)
   ↓
3. Upload Checklist (required)
   ↓
4. AI analyzes Target against Context rules
   ↓
5. Answers checklist questions with evidence
```

## Checklist Format Details

### Supported File Types
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`

### Example Structure

| ID | Question | Category |
|----|----------|----------|
| 1  | Is there a DPO appointed? | Privacy |
| 2  | Are access controls documented? | Security |
| 3  | Is data retention policy defined? | Privacy |

### After AI Analysis

| ID | Question | 🤖 Risposta | 🤖 Confidenza | 🤖 Giustificazione | 📊 Status |
|----|----------|-------------|---------------|-------------------|-----------|
| 1  | Is there a DPO appointed? | Yes, John Doe | 95% | Context Rule: "GDPR Art. 37..."<br>Target Evidence: "Section 3.2 states..." | DRAFT |

## Best Practices
1. Keep questions clear and specific
2. Use consistent ID formatting
3. One question per row
4. Avoid merged cells
5. First row should contain column headers
