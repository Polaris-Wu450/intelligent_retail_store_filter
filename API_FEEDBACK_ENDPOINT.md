# Feedback API Endpoint

## GET /api/feedback/

**Purpose**: List and filter feedback entries with their associated action plans.

### Query Parameters (All Optional)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `category` | string | `FURNITURE`, `ELECTRONICS`, `CLOTHING` | Filter by category code |
| `store_id` | string | e.g., `NYC001`, `CHI001` | Filter by store ID |

### Examples

```bash
# Get all feedback
GET /api/feedback/

# Filter by category
GET /api/feedback/?category=FURNITURE

# Filter by store
GET /api/feedback/?store_id=NYC001

# Combined filter
GET /api/feedback/?category=FURNITURE&store_id=NYC001
```

### Response Format

```json
{
  "feedback": [
    {
      "feedback_id": 8,
      "store_id": "NYC001",
      "store_name": "New York Manhattan Flagship",
      "category_code": "FURNITURE",
      "created_at": "2026-03-24T03:34:09.200122+00:00",
      "status": "completed",
      "action_plan": {
        "id": 38,
        "content": "## 🔴 PROBLEM SUMMARY\n...",
        "created_at": "2026-03-24T03:34:09.201713+00:00",
        "updated_at": "2026-03-24T03:34:21.144703+00:00"
      }
    }
  ],
  "count": 1,
  "filters": {
    "category": "FURNITURE",
    "store_id": "NYC001"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `feedback_id` | integer | Unique feedback ID |
| `store_id` | string | Store identifier (e.g., NYC001) |
| `store_name` | string | Store display name |
| `category_code` | string | Category code (FURNITURE/ELECTRONICS/CLOTHING) |
| `created_at` | datetime | Feedback submission timestamp |
| `status` | string | Action plan status: `pending`, `processing`, `completed`, `failed`, `no_plan` |
| `action_plan` | object/null | Action plan details (null if no plan exists) |
| `action_plan.id` | integer | Action plan ID |
| `action_plan.content` | string/null | Plan content (only if status is `completed`) |
| `action_plan.created_at` | datetime | Plan creation timestamp |
| `action_plan.updated_at` | datetime | Plan last update timestamp |

### Status Values

- `pending` - Action plan created, waiting to be processed
- `processing` - LLM is currently generating the plan
- `completed` - Plan successfully generated (content available)
- `failed` - Plan generation failed
- `no_plan` - No action plan exists for this feedback

### Notes

- Results are ordered by `created_at` descending (newest first)
- Action plan content is only included when status is `completed`
- If a feedback has multiple action plans, only the most recent one is returned
- Category filter is case-insensitive (converts to uppercase)

---

## POST /api/feedback/

**Purpose**: Create new feedback entry and trigger action plan generation.

See existing documentation for POST endpoint details.
