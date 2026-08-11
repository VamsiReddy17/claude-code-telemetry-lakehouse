# Silver / Gold table contracts

## silver.sessions

| Column | Type | Notes |
|--------|------|-------|
| session_id | STRING PK | |
| org_id | STRING | |
| user_account_uuid | STRING | |
| user_email | STRING | optional, from resource attrs |
| app_version | STRING | |
| started_at | TIMESTAMP | |
| last_event_at | TIMESTAMP | |
| prompt_count | BIGINT | |
| response_count | BIGINT | |
| tool_call_count | BIGINT | |
| total_input_tokens | BIGINT | |
| total_output_tokens | BIGINT | |
| total_cost_usd | DOUBLE | |

## silver.prompts

| Column | Type |
|--------|------|
| prompt_sk | STRING (hash session_id+prompt_id+sequence) |
| session_id | STRING |
| prompt_id | STRING |
| event_sequence | BIGINT |
| event_timestamp | TIMESTAMP |
| user_account_uuid | STRING |
| prompt_text | STRING |
| prompt_length | INT |
| org_id | STRING |

## silver.responses

| Column | Type |
|--------|------|
| response_sk | STRING |
| session_id | STRING |
| prompt_id | STRING |
| message_uuid | STRING |
| event_sequence | BIGINT |
| event_timestamp | TIMESTAMP |
| response_text | STRING |
| response_length | INT |
| model | STRING |
| org_id | STRING |

## silver.tool_events

| Column | Type |
|--------|------|
| tool_event_sk | STRING |
| session_id | STRING |
| prompt_id | STRING |
| event_name | STRING |
| tool_name | STRING |
| tool_input | STRING |
| tool_output | STRING |
| decision | STRING |
| event_timestamp | TIMESTAMP |
| org_id | STRING |

## gold.daily_user_usage

| Column | Type |
|--------|------|
| usage_date | DATE |
| org_id | STRING |
| user_account_uuid | STRING |
| sessions | BIGINT |
| prompts | BIGINT |
| responses | BIGINT |
| tool_events | BIGINT |
| input_tokens | BIGINT |
| output_tokens | BIGINT |
| cost_usd | DOUBLE |

## gold.compliance_transcript_lines

Flattened prompt↔response pairs for eDiscovery-style export (PII policy applied).
