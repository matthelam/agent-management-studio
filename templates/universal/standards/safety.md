# Safety Standard

Apply when your output handles data, authentication, or external inputs. Evaluate every change against these criteria.

**Input Validation** — Never trust input. Validate type, length, format, and range at the boundary. Use allowlists over denylists. Reject anything unexpected.

**Authentication** — Verify identity before granting access. Use established protocols (OAuth, JWT, session tokens). Never roll your own auth. Never store plaintext passwords.

**Access Control** — Enforce authorisation server-side. Check permissions on every request. Default to deny. Never rely on client-side checks alone.

**Data Protection** — Encrypt sensitive data at rest and in transit. Never log secrets, tokens, or personally identifiable information. Use parameterised queries — never concatenate user input into SQL.

**Configuration** — Secrets live in environment variables or secret managers, never in source code. Separate configuration from code. Fail securely — errors must not expose internal state.

**Logging** — Log security-relevant events: auth failures, permission denials, input validation rejections. Never log sensitive data. Ensure logs are tamper-evident and retained per policy.
