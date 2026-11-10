# MechTech — Security Baseline

**Version:** 1.0 · **Scope:** Local prototype and preparation for public deployment

## 1. Security posture
MechTech initially processes simulated equipment data. It is not an industrial control system, safety instrument, or certified diagnostic product. Do not connect it to machinery control circuits. Public deployment requires a separate security review.

## 2. Identity
- Hash passwords using Argon2id with maintained library defaults or reviewed parameters.
- Never store plaintext passwords or log credentials.
- Use opaque, cryptographically random session tokens.
- Store only a secure hash of each session token.
- Send session token in an HttpOnly cookie; set Secure in HTTPS and an appropriate SameSite policy.
- Expire and revoke sessions; rotate after authentication-sensitive events.
- Protect cookie-authenticated state changes with CSRF tokens.
- Rate-limit login, registration, and password-change attempts.
- Do not reveal whether an email address exists in public authentication responses.

## 3. Registration and roles
- Public registration always creates a pending account.
- Pending accounts cannot access protected resources.
- Only authorized administrators can approve/reject requests.
- Public users cannot choose privileged roles or organization IDs.
- Admin-created accounts must be audited and require a secure password setup flow.
- Apply least privilege and review permissions regularly.

## 4. Tenant isolation
- Resolve organization access from the authenticated user's memberships.
- Scope every tenant-owned query and mutation by authorized organization.
- Verify nested resource ownership (for example, a sensor belongs to the equipment and organization in the request).
- Do not trust organization IDs supplied by the browser.
- Test cross-organization read, update, delete, upload, and download attempts.

## 5. Input and API protection
- Validate all input with Pydantic and explicit domain constraints.
- Use SQLAlchemy parameterized queries; never concatenate untrusted input into SQL.
- Allowlist sorting and filtering fields.
- Enforce request body, batch, and upload size limits.
- Validate timestamps, units, numeric ranges, and identifiers.
- Use rate limits and abuse controls for public endpoints.
- Return generic errors with request IDs; do not expose stack traces.

## 6. File handling
- Generate server-side storage keys; never use user filenames as filesystem paths.
- Validate extension, media type, and file signature where practical.
- Store files outside publicly served directories.
- Enforce size limits and authorize every download.
- Prevent path traversal and overwrite attacks.
- Keep uploaded content separate from trusted model artifacts.
- Consider malware scanning before public multi-user use.

## 7. Secrets and configuration
- Keep secrets out of source control.
- Provide `.env.example` with placeholders only.
- Validate required environment variables at startup.
- Use separate development and production secrets.
- Never print secrets in logs or exception messages.
- Rotate any credential that may have been committed.

## 8. Browser and transport security
For public deployment:
- HTTPS only.
- Secure cookies.
- Explicit CORS allowlist.
- Appropriate Content Security Policy and security headers.
- Restrict trusted hosts.
- Avoid wildcard credentialed CORS.
- Keep dependencies patched.

## 9. Logging and audit
Record security-relevant events: login success/failure, session revocation, registration decisions, role changes, access denials, file operations, and diagnosis review. Do not log passwords, session tokens, API keys, or unnecessary personal data. Restrict audit-log access and protect integrity.

## 10. Minimum release gate
- [ ] No secrets in repository or build artifacts.
- [ ] Password hashing and session lifecycle tested.
- [ ] CSRF protection tested.
- [ ] Role and object-level permissions tested.
- [ ] Cross-tenant access tests pass.
- [ ] Upload validation and authorization tested.
- [ ] Rate limits and request limits configured.
- [ ] HTTPS, CORS, and secure cookies configured for public deployment.
- [ ] Database and file backups tested.
- [ ] Dependency and configuration review completed.
- [ ] Diagnostic outputs clearly labeled advisory and require human review.
