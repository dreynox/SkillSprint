# Authentication Rate Limiting

SkillSprint protects authentication and password-reset endpoints with a
lightweight in-memory rate limiter. No Redis service is required for local
development.

## Protected endpoints

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/forgot-password/request-otp`
- `POST /auth/forgot-password/verify-otp`

## Default policy

| Operation | Default |
|---|---:|
| Failed login per requester + account | 5 failures / 10 minutes |
| Failed login per account across requesters | 20 failures / 10 minutes |
| Registration | 10 requests / hour per requester |
| OTP request | 3 requests / 15 minutes per requester + normalized email |
| OTP verification HTTP bucket | 5 attempts / 15 minutes per requester + normalized email |
| OTP record attempt limit | 5 invalid attempts per stored OTP |

All values are configurable through environment variables:

```env
OTP_MAX_ATTEMPTS=5

AUTH_LOGIN_RATE_LIMIT=5
AUTH_LOGIN_ACCOUNT_RATE_LIMIT=20
AUTH_LOGIN_RATE_WINDOW_SECONDS=600

AUTH_REGISTER_RATE_LIMIT=10
AUTH_REGISTER_RATE_WINDOW_SECONDS=3600

AUTH_OTP_REQUEST_RATE_LIMIT=3
AUTH_OTP_REQUEST_RATE_WINDOW_SECONDS=900

AUTH_OTP_VERIFY_RATE_LIMIT=5
AUTH_OTP_VERIFY_RATE_WINDOW_SECONDS=900

AUTH_TRUSTED_PROXY_HOPS=1
```

All rate-limit and window values are validated as positive integers at startup.
Invalid configuration fails fast instead of producing request-time 500 errors.

`OTP_MAX_ATTEMPTS` and `AUTH_OTP_VERIFY_RATE_LIMIT` are intentionally separate:

- `OTP_MAX_ATTEMPTS` limits invalid attempts stored on one
  `PasswordResetOTP` database record and consumes that OTP when exhausted.
- `AUTH_OTP_VERIFY_RATE_LIMIT` limits HTTP verification requests for a
  requester + normalized email within the configured time window.

These values may differ.

## Response behavior

When a bucket is blocked, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 300
```

```json
{
  "detail": "Too many requests. Please try again later."
}
```

## Login protections

Login uses two buckets:

1. requester + normalized account, limiting one requester attacking one account;
2. account-only, limiting distributed attempts against the same account.

Failed attempts increment both buckets. A successful login clears both.

Password verification is still executed for unknown accounts using a
module-level dummy password hash. This reduces simple account-enumeration
timing differences between a missing account and a wrong password.

The login flow intentionally remains split into `check()` then `record()`
because only failed authentication consumes capacity. This is a soft limit
under extreme concurrency. Registration and OTP request endpoints, where every
request consumes capacity, use atomic `consume()` instead.

## Registration race handling

The application keeps the existing email pre-check but also catches
`IntegrityError` during commit. Concurrent registrations that race on the
unique email constraint are rolled back and receive the same generic response.

## Password-reset request privacy

Password-reset request responses are identical for existing and unknown emails:

```text
If an account exists for that email, a password-reset OTP has been sent.
```

Both paths perform the active-code lookup, OTP hash generation, comparable
database write/commit work, and return the same response. Unknown-account decoy
rows are inserted and deleted in the same transaction and use an HMAC-derived
placeholder rather than storing the supplied unknown email.

The repository does not currently include a durable task queue. SMTP delivery
therefore uses FastAPI `BackgroundTasks` as the non-blocking fallback.
Delivery failures are caught and logged without the email address, OTP, SMTP
credentials, or provider exception text.

## Proxy/client IP handling

Rate limiting trusts `X-Forwarded-For` only when the direct connection comes
from a private/loopback proxy (as in Render-style reverse-proxy deployment).
Addresses are validated with `ipaddress`, and the configured number of trusted
hops is selected from the **right side** of the chain. The spoofable leftmost
entry is never blindly selected.

Direct public peers ignore `X-Forwarded-For`.

## Key privacy

In-memory keys use HMAC-SHA256 with `SECRET_KEY`, rather than plain SHA-256.
Low-entropy requester IPs and email addresses therefore cannot be recovered
from a copied key set through straightforward offline enumeration.

## Stale-key cleanup

The in-memory store records each key's window duration. `RateLimiter`
periodically calls the store's optional `prune_expired()` method so one-off
emails do not remain in memory indefinitely. A future Redis store does not need
to implement this method because native key expiry can be used instead.

## Storage architecture

`RateLimiter` still depends on the `RateLimitStore` protocol, allowing a later
shared Redis implementation without changing endpoint behavior.

## Testing

```powershell
cd backend
python -m pytest tests/test_auth_rate_limiting.py -v
```

Tests use an injectable fake clock and do not wait in real time.
