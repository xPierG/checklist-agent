# Checklist Excel Format Specification
# Checklist Format Guide

## Document Types

The Checklist Agent works with **three types of documents**:

### 1. 📚 Context Documents (Regulations/Policies)
**Purpose**: Define the rules and compliance requirements

**Supported File Types**: PDF, DOCX, TXT

**Examples**:
- GDPR regulation (PDF)
- ISO 27001 standard (DOCX)
- Company security policy (TXT)
- Industry best practices

**Upload**: In sidebar under "Context Documents"
**Optional**: Yes, but recommended for accurate compliance verification

### 2. 📋 Checklist (Excel/CSV)
**Purpose**: Contains the questions to verify

**Required Columns**:
- **ID Column**: `ID`, `Item_ID`, `Number`, `No`, or `#`
- **Question Column**: `Question`, `Requirement`, `Item`, `Description`, `Check`, or `Domanda`
- **Description Column** (optional): `Description`, `Descrizione`, `Details`, `Dettagli`, `Note` (Provides context for the AI)
- **Category** (optional): For grouping questions

**Note**: Rows where the Question is empty will be automatically filtered out.

**Auto-Generated Columns** (added by AI, can be manually edited):
- `Risposta`: Direct answer to the question (AI-generated, editable)
- `Original_Risposta`: The initial AI-generated answer (read-only, for comparison)
- `Confidenza`: Confidence score (0-100%)
- `Spiegazione`: Detailed justification with text snippets (AI-generated, editable)
- `Status`: PENDING → DRAFT → APPROVED/REJECTED
- `Manually_Edited`: Boolean flag, `True` if `Risposta` or `Spiegazione` has been manually changed.
- `Discussion_Log`: Chat history for each item

### 3. 📄 Target Documents (To Analyze)
**Purpose**: The actual content being verified for compliance

**Supported File Types**: PDF, DOCX, TXT

**Examples**:
- Company privacy manual (PDF)
- Security procedures document (DOCX)
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
   (Uses Question + Description for context)
   ↓
5. Answers checklist questions with evidence
```

## Checklist Format Details

### Supported File Types
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`

### Example Structure

| ID | Domanda | Descrizione | Category |
|----|----------|-------------|----------|
| 1  | Is there a DPO appointed? | Check for name and contact info | Privacy |
| 2  | Are access controls documented? | Look for password policies | Security |
| 3  | Is data retention policy defined? | Check retention periods | Privacy |

### After AI Analysis

| ID | Domanda | 🤖 Risposta AI | 🤖 Confidenza Risposta | 🤖 Spiegazione | 📊 Status |
|----|----------|-------------|---------------|-------------------|-----------|
| 1  | Is there a DPO appointed? | Yes, John Doe | 95% | Context Rule: "GDPR Art. 37..."<br>Target Evidence: "Section 3.2..." | DRAFT |

## Best Practices
1. Keep questions clear and specific
2. Use consistent ID formatting
3. One question per row
4. Avoid merged cells
5. First row should contain column headers
