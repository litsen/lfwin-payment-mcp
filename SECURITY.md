# Security Policy

## Supported Versions

Security fixes are provided for the latest published version.

## Reporting a Vulnerability

Please do not open public GitHub issues for sensitive vulnerabilities.

Report security issues by contacting the maintainers through the project repository owner profile.

## Credential Handling

This MCP server requires customer-provided payment credentials:

- `PAYMENT_API_KEY`
- `PAYMENT_SIGN_KEY`

Do not commit real credentials to GitHub. Use environment variables, IDE secret storage, or the MCP client's secure configuration mechanism.

## Deployment Notes

The default MCP transport is `stdio`, intended for local clients and container-based inspection. If you expose this server remotely, add authentication, tenant isolation, access control, and Origin validation.
