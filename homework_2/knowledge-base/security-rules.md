# Security Rules

- Do not build SQL queries by string concatenation. Use parameterized queries.
- Do not read arbitrary filesystem paths from user input.
- Do not log tokens, webhook secrets, passwords, or Slack webhook URLs.
- Verify GitHub webhook signatures before processing pull request payloads.
- Minimize IAM permissions and remove demo resources after testing.
