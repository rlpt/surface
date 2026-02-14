# Issuing Shares to Early Supporters

How to set up a small share pool and issue shares to advisors, early supporters, and pre-investment contributors. The mechanics, the tax, the traps.

---

## First decision: shares or options?

You have two mechanisms. They are fundamentally different.

| | Shares | Options |
|---|--------|---------|
| **What they get** | Actual shares — they are a shareholder immediately | The right to buy shares later at a fixed price |
| **When they become a shareholder** | Now | When they exercise the option (which may be years away) |
| **Tax for them** | Taxed now on the market value of what they receive (minus what they pay) | No tax on grant. Tax on exercise (or on sale, depending on the scheme) |
| **Voting rights** | Yes — they can vote from day one | No — not a shareholder until exercise |
| **Pre-emption / transfer restrictions** | They are bound by the articles immediately | Not relevant until exercise |
| **Complexity** | Simpler to set up | Requires an option scheme (EMI, unapproved, or CSOP) |
| **SEIS/EIS impact** | They become shareholders — check connected person rules | No impact until exercise |
| **Best for** | Co-founders, very early contributors who should have skin in the game now | Advisors, supporters, future hires |

**For early supporters, shares are usually simpler and more appropriate.** Options are better for employees and people who will contribute over time. The rest of this guide covers shares.

---

## The steps, in order

### Step 1: Adopt bespoke articles FIRST

**Do not issue shares to anyone while Model Articles are in force.**

Model Articles have almost no transfer restrictions. A supporter could receive shares and immediately transfer them to anyone — a competitor, an ex-partner, a random third party. You would have no right to buy them back and no pre-emption rights.

The bespoke articles (in `articles-of-association.md`) include:
- Pre-emption rights on transfer (articles 25-32)
- Drag-along and tag-along (articles 33-34)
- Leaver / vesting provisions (articles 35-40)
- Board approval of transfers (article 31)

These must be in place before the first share goes to anyone other than you.

**Process**: pass a special resolution to adopt the bespoke articles, file CC04 at Companies House. You hold 100% of votes, so you pass it alone. Do this before step 2.

### Step 2: Decide the pool size

Common pool sizes for early supporters (pre-investment):

| Pool size | Typical use |
|-----------|-------------|
| 1-2% | Individual advisor (meets monthly, makes introductions) |
| 0.25-1% | Early supporter (gave feedback, opened doors, helped with a specific problem) |
| 5-10% | Option pool reserved for future hires (investors will expect this, but it is usually created at investment, not now) |
| 2-5% total | Aggregate for all early supporters combined |

**Keep the total small.** Every share you issue now dilutes you. Investors will look at your cap table and ask why 10% is already gone before they arrived. 2-5% total across all early supporters is reasonable. More than that raises questions.

**Be specific about what each person contributed.** "They helped early on" is vague. "They introduced us to our first three pilot customers" or "they advised on the EAV architecture and attended monthly calls for 6 months" is defensible.

### Step 3: Value the shares

The shares have a market value. For tax purposes, HMRC will want to know what that value is. At pre-revenue, just incorporated, no investment, the market value should be very low — potentially just the nominal value (£0.0001 per share if that is your share structure).

**How to establish value:**

| Method | When to use |
|--------|------------|
| **Nominal value** | Just incorporated, no revenue, no investment, no significant assets. The shares are worth their nominal value (e.g. £0.0001 each). This is defensible if the company genuinely has no value yet. |
| **HMRC valuation (SAV)** | If you are unsure, you can ask HMRC's Shares and Assets Valuation team to agree a value. Free, but takes 4-6 weeks. Gives certainty. |
| **Independent valuation** | If the company has raised money, has revenue, or has significant IP. An accountant or valuer determines the market value. |
| **Last round price** | If you have already raised investment, the price per share from the last round is a strong indicator of market value. |

**At your stage (just incorporated, pre-trading, no investment):** the shares are worth nominal value or very close to it. The supporter pays nominal value per share (e.g. 10,000 shares x £0.0001 = £1.00). No tax issue because they paid market value.

**The danger**: if you issue shares to a supporter after the company has built significant product, acquired customers, or raised money, HMRC may argue the market value is higher than nominal. The supporter would owe income tax on the difference between what they paid and the market value. This is why timing matters — issue early, when the value is genuinely low.

### Step 4: Section 431 election

When you issue shares that are subject to restrictions (vesting, leaver provisions, transfer restrictions), the shares are technically "restricted securities" under the Income Tax (Earnings and Pensions) Act 2003 (ITEPA), sections 423-432.

Without a s.431 election, HMRC can tax the supporter again when restrictions are lifted (e.g. when shares vest). The s.431 election tells HMRC: "tax me on the unrestricted market value now, and don't tax me again later."

**In practice**: at nominal value, the tax is zero either way. But you should still file the election because:
- It creates certainty — no future tax surprises
- Investors and their solicitors will ask "were s.431 elections filed?" during due diligence
- It costs nothing to file

**How**: both parties (the company and the recipient) sign the election within 14 days of the share issue. Keep a copy. It is a one-page form.

### Step 5: Authority to allot (s.551 Companies Act 2006)

The directors need authority from shareholders to allot new shares. This is granted by ordinary resolution.

As sole shareholder, you pass this resolution yourself. The resolution should:
- Authorise the directors to allot shares up to a specified amount (e.g. "up to [X] ordinary shares")
- Specify the period of authority (typically 5 years)
- Cover the specific allotment you are about to make

**Template resolution:**

> The sole member of the Company RESOLVES as an ordinary resolution that, pursuant to section 551 of the Companies Act 2006, the directors are generally and unconditionally authorised to allot shares in the Company up to an aggregate nominal amount of £[AMOUNT] for a period of five years from the date of this resolution, such authority being in addition to any existing authority.

### Step 6: Disapplication of statutory pre-emption rights (s.561)

Under the Companies Act, when a company issues new shares for cash, it must first offer them to existing shareholders in proportion to their holdings. Since you are the only shareholder, you need to disapply this right so the shares can go directly to the supporter.

This requires a special resolution (75% — which you pass alone as 100% shareholder).

**Template resolution:**

> The sole member of the Company RESOLVES as a special resolution that, pursuant to section 569 of the Companies Act 2006, the directors are empowered to allot equity securities for cash pursuant to the authority granted by [the s.551 resolution above] as if section 561 of the Act did not apply to any such allotment, such power to expire at the end of the period of authority granted under that resolution.

### Step 7: Subscriber's letter / share subscription agreement

A short agreement between the Company and the supporter covering:

| Term | What to include |
|------|----------------|
| **Parties** | The Company and the supporter |
| **Shares** | Number of shares, class (ordinary), nominal value |
| **Subscription price** | What the supporter pays per share (usually nominal value at this stage) |
| **Vesting** | The vesting schedule (see below) |
| **Restrictions** | Reference to the articles — pre-emption, transfer restrictions, leaver provisions all apply |
| **Deed of adherence** | The supporter signs the deed of adherence to the articles (Schedule 2 of the bespoke articles) |
| **s.431 election** | Both parties sign the election (attached as a schedule) |
| **Warranties** | The supporter warrants they are acquiring the shares for their own account, not as nominee |
| **Confidentiality** | The terms of the arrangement are confidential |

This does not need to be long. 3-5 pages plus the deed of adherence and s.431 election as schedules.

### Step 8: Vesting schedule

Shares issued to supporters should vest over time. If a supporter disappears after a month, you do not want them holding unrestricted shares. The vesting schedule and leaver provisions in the bespoke articles (articles 35-40) provide the mechanism.

**Typical vesting for advisors/supporters:**

| Type | Schedule |
|------|----------|
| **Advisor (ongoing)** | 24 months, monthly vesting, no cliff. Conditional on continued advisory services. |
| **Early supporter (contribution complete)** | Immediate vesting on all shares. If their contribution is already done and you are rewarding past work, vesting is not appropriate — they have already earned it. |
| **Hybrid** | 50% immediate (for past contribution), 50% over 12-24 months (for ongoing involvement). |

**The leaver provisions in the articles apply automatically.** If a supporter with unvested shares stops being involved:
- Good Leaver: unvested shares bought back at Fair Market Value
- Bad Leaver: unvested shares bought back at nominal value

"Good Leaver" for a supporter would need to be defined in the subscription agreement (since the articles define it in terms of employment/directorship). Typically: a supporter is a Good Leaver if they have fulfilled their advisory obligations and are leaving amicably.

### Step 9: Board resolution to allot

Pass a board resolution (you, as sole director) resolving to:
- Allot [number] ordinary shares of £[nominal value] each to [supporter name]
- At a subscription price of £[price] per share
- Subject to the terms of the subscription agreement
- Conditional on the supporter signing the deed of adherence and s.431 election

Record this in formal board minutes. Declare your interest under s.177 if the supporter is someone you have a personal relationship with (friend, family).

### Step 10: Execution day

On the same day:

1. Supporter signs the subscription agreement
2. Supporter signs the deed of adherence (Schedule 2 of the articles)
3. Both parties sign the s.431 election
4. Supporter pays the subscription price (even if it is £1 — the payment must actually happen)
5. Board resolution records the allotment
6. Update the register of members

### Step 11: File at Companies House

Within **one month** of allotment, file form **SH01** (return of allotment of shares) at Companies House. This notifies Companies House that new shares have been issued. Include:
- Number of shares allotted
- Class of shares
- Nominal value
- Amount paid (including any premium)
- Name and address of the allottee

### Step 12: Issue share certificate

Within **two months** of allotment, issue a share certificate to the supporter. The certificate states:
- Company name and number
- Name of shareholder
- Number and class of shares
- Amount paid up
- Signed by a director

### Step 13: File s.431 election

Keep the signed s.431 election with the company's records. You do not file it with HMRC proactively — but you must produce it if HMRC asks, and the supporter must reference it on their self-assessment return if they report a chargeable event.

### Step 14: Update cap table

Update your cap table spreadsheet to reflect the new shareholder, their shares, their vesting schedule, and the dilution to your holding.

### Step 15: Notify your accountant

Tell your accountant that you have issued shares. They may need to:
- Report it on the company's annual return of securities (form 42, filed with HMRC)
- Include it in the company's annual accounts
- Advise the supporter on their personal tax position

---

## Tax implications — summary

### For the supporter

| Scenario | Tax consequence |
|----------|----------------|
| Pays market value for the shares | No income tax. No NI. They bought shares at fair price. |
| Pays less than market value (e.g. nominal value when market value is higher) | Income tax on the difference (market value minus price paid), treated as employment income or miscellaneous income. NI may also apply. |
| Shares subject to restrictions (vesting) without s.431 election | Taxed now on restricted value, taxed again when restrictions lift. Bad outcome. |
| Shares subject to restrictions with s.431 election | Taxed now on unrestricted value. No further tax on restriction lifting. |
| Sells shares later for a profit | Capital gains tax on the gain (sale price minus acquisition cost). Annual CGT exemption applies (currently £3,000). |

**At your stage**: market value is nominal. Supporter pays nominal value. With s.431 election filed. Tax consequence: zero.

### For you (dilution, not tax)

Issuing shares to a supporter is not a taxable event for you. You are diluted (your percentage decreases) but you do not owe tax on that dilution. Dilution is an economic cost, not a tax cost.

### For the company

No corporation tax consequence from issuing shares at market value. If you issue shares at below market value to someone who provides services (an advisor), the company may be able to claim a corporation tax deduction for the cost of the services received. Your accountant can advise.

---

## SEIS/EIS implications

### Does issuing supporter shares affect SEIS/EIS qualification?

**Probably not, but check.**

- **Gross assets test (SEIS)**: must be under £350k. Issuing shares at nominal value adds almost nothing to gross assets.
- **Number of employees**: supporters are not employees unless you put them on payroll. Advisory relationships do not count.
- **Connected persons**: a supporter who holds 30%+ of the company's shares after issue would be a "connected person" and could not claim SEIS/EIS relief on their own investment. At 1-2% this is not an issue.
- **Share class**: supporter shares should be the same class of ordinary shares that SEIS/EIS investors will receive (or a separate class, but not preferred). Keep it simple — issue the same ordinary shares.
- **Prior investment**: issuing shares to supporters is not "investment under EIS or VCT" — it does not trigger the "no prior qualifying investment" test for SEIS.

**The main risk**: if a supporter is also a potential investor, they are now a shareholder. Their SEIS/EIS eligibility depends on their percentage holding (must be under 30%) and whether they are an employee or director (connected person test). Check each supporter individually.

---

## Cap table example

Before supporter shares:

| Shareholder | Shares | % |
|-------------|--------|---|
| Richard Targett | 1,000,000 | 100% |

After issuing 2% supporter pool (split between two people):

| Shareholder | Shares | % |
|-------------|--------|---|
| Richard Targett | 1,000,000 | 98.04% |
| Advisor A | 10,000 | 0.98% |
| Supporter B | 10,000 | 0.98% |
| **Total** | **1,020,000** | **100%** |

Note: you issued 20,000 new shares. You did not transfer your existing shares. Your absolute number of shares stays the same — your percentage decreases because the total increased. This is dilution by issuance, not transfer.

After a £350k SEIS round at £3.5m pre-money (10% dilution):

| Shareholder | Shares | % |
|-------------|--------|---|
| Richard Targett | 1,000,000 | 88.24% |
| Advisor A | 10,000 | 0.88% |
| Supporter B | 10,000 | 0.88% |
| SEIS Investors | 113,333 | 10.00% |
| **Total** | **1,133,333** | **100%** |

Everyone dilutes proportionally when new shares are issued.

---

## Common mistakes

1. **Issuing shares before adopting bespoke articles.** The supporter now holds shares with no transfer restrictions, no pre-emption rights, and no leaver provisions. Very hard to fix retroactively.

2. **Not filing the s.431 election within 14 days.** The window is strict. If you miss it, the supporter faces potential double taxation on restricted shares.

3. **Not filing SH01 within one month.** Late filing is a criminal offence (though rarely prosecuted for short delays). File promptly.

4. **Giving too much equity.** 5% to an advisor who "promised to help" but has no binding commitment. When they disappear, you have a 5% shareholder you cannot get rid of. Keep individual allocations small (0.5-2%) and attach vesting.

5. **No vesting on shares for ongoing involvement.** If the deal is "advise us for 2 years," the shares should vest over 2 years. If the advisor stops after 3 months, you can buy back the unvested shares.

6. **Verbal agreements.** "I'll give you some shares" with no written terms. Six months later, you disagree on how many, on what terms, subject to what conditions. Get it in writing before issuing.

7. **Not considering the investor's perspective.** Before your first round, an investor will look at the cap table and ask about every shareholder. "Who is Advisor A? What do they do? Why do they have 3%?" Have clear answers.

8. **Forgetting to tell your accountant.** The company has a reporting obligation (form 42) for share issues to directors and employees. Even if the supporter is neither, tell your accountant so they can advise on reporting.

---

## Document checklist

For each supporter share issue, you need:

- [ ] Bespoke articles adopted (one-time, before first issue)
- [ ] s.551 authority to allot (shareholder ordinary resolution)
- [ ] s.561 disapplication of pre-emption (shareholder special resolution)
- [ ] Subscription agreement / subscriber's letter (signed by both parties)
- [ ] Deed of adherence (signed by supporter — Schedule 2 of articles)
- [ ] s.431 election (signed by both parties, within 14 days)
- [ ] Board resolution to allot (board minutes)
- [ ] Register of members updated
- [ ] SH01 filed at Companies House (within 1 month)
- [ ] Share certificate issued (within 2 months)
- [ ] Cap table updated
- [ ] Accountant notified
- [ ] Signed documents scanned and uploaded to Google Drive (`01 Corporate/` and `02 Legal/`)
