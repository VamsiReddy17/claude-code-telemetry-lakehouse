# 04. Failure Handling and Best Practices

When operating inline security hooks, robustness and clear fallback mechanisms are critical to balancing security with availability.

---

## ⚠️ Failure Modes

During operation, several failure conditions might occur when Anthropic attempts to contact your security endpoint:
- **Server Unreachable**: Your endpoint is down, experiencing DNS issues, or blocking Anthropic's IPs.
- **Server Timeout**: Your endpoint takes longer than the configured timeout (default 5s) to return a verdict.
- **Invalid Response**: Your endpoint returns a non-200 HTTP status, malformed JSON, or an unrecognized verdict schema.

---

## 🛡️ Failure Policies

When a failure mode occurs, Anthropic will fall back to your configured **Failure Policy**. You must choose one of the following approaches based on your organization's risk tolerance:

| Policy | Behavior on Failure | Use Case |
| :--- | :--- | :--- |
| **Fail Closed** | Blocks all requests if the security server is unavailable. | **High Security**: Choose this if preventing data exfiltration is more critical than maintaining uptime. |
| **Fail Open** | Allows all requests to proceed if the security server is unavailable. | **High Availability**: Choose this if maintaining user productivity is preferred during security infrastructure outages. |

> [!CAUTION]
> If you select **Fail Closed**, any outage on your security server will completely block users from using Claude. Ensure your endpoint has high availability.

---

## 💡 Best Practices

To ensure a smooth deployment and optimal operation of Inference Hooks, follow these guidelines:

1. **Start with Shadow Mode**: Always begin in shadow mode. Do not jump straight to full enforcement. 
2. **Test with Representative Traffic**: Validate your policies against real user prompts before enforcing blocks.
3. **Monitor False Positive Rates**: Regularly review denied prompts. High false positive rates will severely impact user trust and productivity.
4. **Set Appropriate Timeout Values**: Ensure the timeout allows your DLP scanner to finish, but keeps the user experience snappy. 5 seconds is standard, but highly complex regex scanning may require more time.
5. **Ensure High Availability**: If using "fail closed", your webhook endpoint must be deployed across multiple availability zones with auto-scaling to handle peak traffic.
6. **Implement Signature Verification**: Strictly enforce Standard Webhooks signature verification to prevent spoofed payloads.
7. **Log All Verdicts**: Maintain a centralized audit trail of all webhook requests and your server's corresponding verdicts for compliance reporting.

---

## 🔒 Security Considerations

- **Secure the Endpoint**: Ensure your webhook endpoint only accepts HTTPS traffic over TLS 1.2 or higher.
- **Rotate Secrets**: Regularly rotate the webhook signing secrets according to your company's security cadence.
- **Avoid Logging Sensitive Payloads**: While you should log verdicts, be careful not to log the raw prompt content in plain text if it contains the very PII or sensitive data you are trying to protect.

---
*Return to: [01. Overview and Core Concepts](01_overview_and_concepts.md)*
