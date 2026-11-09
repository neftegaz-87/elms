---
execution: direct-ad-hoc
date: 2026-11-05
role: APP
mode: BUGFIX
slug: yandex-oauth-scope
status: done
---

# Yandex OAuth `invalid_scope`

## Root cause

Keycloak's standard `oidc` broker forcibly prepends `openid` to the configured
scope. Yandex ID OAuth accepts `login:email login:info`, but does not accept
`openid`, so the authorization request failed after the callback URL had
already been corrected.

## Fix

- Added the `yandex-oauth` Keycloak provider based on the OAuth 2.0 broker
  contract. It sends the configured Yandex scopes unchanged and reads the
  Yandex profile with the `OAuth` authorization scheme.
- Packaged the provider into the custom Keycloak image and switched the realm
  broker from `oidc` to `yandex-oauth`.
- Updated the Yandex onboarding documentation with the required permissions.

## Evidence

- Custom Keycloak image build: PASS.
- Keycloak startup registered `yandex-oauth` provider: PASS.
- Live admin realm update recreated alias `yandex` with provider `yandex-oauth`:
  HTTP 201.
- Live authorization trace now reaches Yandex with exactly
  `scope=login:email login:info`; `openid` is absent.
- Targeted SSO/UI tests: 27 passed.
- Infrastructure regression tests: 38 passed.

Interactive Yandex credentials were not entered by the agent; the final
credential exchange remains an operator/browser check.
