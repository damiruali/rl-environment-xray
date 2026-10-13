# Public Data Policy

Agent X-Ray is a public, domain-neutral research and engineering project. Its repository
must remain safe to clone, inspect, and redistribute.

## Allowed material

- fictional or programmatically generated tasks and records;
- synthetic identifiers with no relationship to real people or organizations;
- public standards and documentation cited by URL;
- redacted model traces produced specifically for this public project;
- configuration examples containing placeholder values only.

## Prohibited material

- employer, client, partner, or customer data;
- real support tickets, conversations, documents, policies, or knowledge-base content;
- internal schemas, endpoints, hostnames, credentials, tokens, or infrastructure details;
- personal data or identifiers copied from private systems;
- code or prompts copied from confidential work;
- artifacts derived from private data, even when obvious names were removed.

Generic concepts such as approvals, access control, retries, and escalation may be modeled,
but their implementation must be created independently for this repository.

## Contribution checklist

Before committing a fixture, trajectory, screenshot, or report:

1. Confirm that its source is synthetic or publicly licensed.
2. Search the staged diff for names, email addresses, phone numbers, account identifiers,
   internal domains, and credentials.
3. Verify that model reasoning and provider metadata are redacted where required.
4. Stage only the intended files; do not use broad staging commands in a workspace that
   contains private output.
5. Run the project acceptance and secret checks.

If prohibited data is discovered, stop publication, remove it from the working tree and
Git history as appropriate, rotate any exposed credential, and document the remediation
without reproducing the sensitive value.
