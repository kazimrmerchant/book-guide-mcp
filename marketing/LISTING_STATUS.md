# Listing status (2026-07-16)

Driven via **owned Chrome CDP** while you were logged in.

## Done without further action

| Channel | Status |
|---------|--------|
| GitHub public repo | Live — https://github.com/kazimrmerchant/book-guide-mcp |
| awesome-mcp-servers | **PR open** — https://github.com/punkpeye/awesome-mcp-servers/pull/10233 |
| GitHub topics / description | MCP + IDE tags including Google Antigravity |
| Launch kit copy | `marketing/PRODUCT_HUNT.md`, `marketing/LAUNCH_KIT.md` |

## Product Hunt — blocked on email verification

**What we completed in Chrome:**

- Opened Product Hunt while signed in (Google + GitHub connected)
- Filled onboarding: name **Kazim Merchant**, headline, categories (AI Coding Agents, etc.)
- Reached “Almost there…” people/products to follow
- **Submit product is gated** until email is confirmed

**Banner on site:**  
`Please check your email to confirm your account. Resend verification`

### Your steps (≈2 minutes)

1. Open the **Product Hunt confirmation email** for the Google account you used (`kazim.r.merchant@gmail.com` likely).
2. Click **confirm / verify**.
3. Go to https://www.producthunt.com/posts/new  
4. Paste from `marketing/PRODUCT_HUNT.md`:
   - URL: `https://github.com/kazimrmerchant/book-guide-mcp`
   - Name / tagline / description
   - Pricing: **Free**
   - Gallery: `docs/assets/book-guide-infographic-hero.png`
5. Post maker comment from `marketing/LAUNCH_KIT.md`

Optional: best launch window **Tue/Wed 12:01 AM PT**.

## mcp.so — signed in; free submit one click away

**What we completed:**

- Google OAuth to mcp.so (account chooser: Kazim Raza / merchant)
- Session cookie present (`__Secure-better-auth.session_token`)
- Submit page: filled repository URL  
  `https://github.com/kazimrmerchant/book-guide-mcp`
- Selected **Free submission** path (queued review)
- UI showed **“Confirm and join the queue”** (free CTA)

Automation could not reliably fire the final confirm (dynamic UI / intercepts). **You click once.**

### Your steps (≈30 seconds)

1. Open https://mcp.so/submit?type=server (same Chrome profile)
2. Confirm repo URL is the book-guide-mcp GitHub link
3. Keep **Free submission** selected (not $39 paid)
4. Click **Confirm and join the queue** / free submit
5. Screenshot success if shown

## Already propagating

- **Glama / PulseMCP-style crawlers** — GitHub topics `mcp` + public README; may appear after index
- **Official MCP Registry** — needs PyPI publish first (`marketing/server.json` ready)

## After you finish PH email + mcp.so click

Reply **“done”** and I can:

- Verify the mcp.so listing URL  
- Draft Show HN / social posts  
- Publish to PyPI + official MCP Registry (if you approve PyPI credentials flow)
