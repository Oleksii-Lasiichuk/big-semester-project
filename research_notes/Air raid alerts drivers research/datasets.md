# Datasets for Analyzing Ukrainian Air-Raid Alerts and Their Drivers (as of 19 Nov 2026)

Liveness checks: HTTP and GitHub/Kaggle/HF API calls run 2026-11-19. "Verified live" means a 200 response or fresh metadata that day. Claims marked (background) come from prior knowledge, not a source fetched today. Treat them as unverified.

## Q1. Which air-raid alert datasets and APIs can be used, and how?

### Takeaway
The Vadimkin GitHub dataset is the best fit for students on Databricks Free Edition. It is MIT-licensed, updated daily, about 31 MB of CSV, and has no registration. The alerts.in.ua API needs a requested token, its history endpoint covers only the last month at 2 requests/min, and it is best used for live top-ups. The ukrainealarm.com API returned 403 without a key.

### Cited Findings
**Vadimkin/ukrainian-air-raid-sirens-dataset** (https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset)
- Access: raw CSV over HTTPS from GitHub, no auth. Example: https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/official_data_en.csv — [datasets README](https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/README.md)
- Verified live: last push 2026-11-19T06:35Z. Files: official_data_en.csv (~31.0 MB), official_data_uk.csv (~41.3 MB), volunteer_data_en.csv (~9.5 MB), volunteer_data_uk.csv (~11.8 MB). Repo total ~727 MB, including geojson and history, so fetch single files rather than cloning — [GitHub API](https://api.github.com/repos/Vadimkin/ukrainian-air-raid-sirens-dataset)
- Schema (official): `oblast, raion, hromada, level, started_at, finished_at, source`. Times are UTC. — [CSV header](https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/official_data_en.csv)
- Coverage: the official data starts 2022-03-15. The volunteer data comes from the eTryvoga channel, starts 2022-02-25, and is oblast-level only. Volunteer alerts with no recorded end are flagged `naive=True` and given a 30-minute duration. — [README](https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/README.md)
- **Granularity break:** since December 2025, alerts are mostly issued per raion (district) rather than per oblast. — [README](https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/README.md), citing [texty.org.ua](https://texty.org.ua/fragments/116501/)
- Bias: two permanent alerts are excluded from the files: Luhansk (since 4 Apr 2022) and Crimea (since 10 Dec 2022). Updated daily. License MIT. — [README](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset)

**alerts.in.ua API** (https://devs.alerts.in.ua/)
- REST/JSON at https://api.alerts.in.ua. It needs a personal token requested through alerts.in.ua/api-request, passed as `?token=` or a Bearer header. Rate limits: soft 8–10 and hard 12 requests/min per IP, with HTTP 429 and possible bans if exceeded. — [docs](https://devs.alerts.in.ua/)
- History: `/v1/regions/{uid}/alerts/month_ago.json` returns only the last month and is limited to 2 requests/min. The docs name no data license. Use is at your own risk, data can be delayed, and the service is volunteer-run. — [docs](https://devs.alerts.in.ua/)

**ukrainealarm.com API** (https://api.ukrainealarm.com)
- The swagger page and `/api/v3/alerts` both returned HTTP 403 without a key on 2026-11-19, so I could not inspect terms or history. (Background: an API key is requested from the site, and the API serves official alert state plus some history per region.)

### Inferences
- Use Vadimkin as the historical backbone, loaded with `pandas.read_csv(url)` and then written to Delta. The 2022–2026 history fits easily within Free Edition limits.
- Any time series must handle the December 2025 oblast-to-raion switch, for example by aggregating to the oblast level ("any raion alerted").

### Gaps
- ukrainealarm.com key process, terms and history depth were not verifiable (403).
- The exact UTC timestamp of Vadimkin's last data row was not checked.

## Q2. What attack, loss and conflict-event datasets exist (Kaggle, ACLED, UCDP, VIINA)?

### Takeaway
Petro Ivaniuk's Kaggle datasets are small, current and licensed CC BY-NC-SA 4.0. They are the most direct "driver" data on missiles and drones launched or intercepted, though the Air Force reporting gap from August 2026 affects the missile data. ACLED's Research tier comes with a 12-month lag. UCDP's API now needs a token. VIINA is a fresh, free alternative.

### Cited Findings
**Kaggle "Massive Missile Attacks on Ukraine"** (https://www.kaggle.com/datasets/piterfm/massive-missile-attacks-on-ukraine)
- Status: last updated 2026-11-14, version 219, about 0.94 MB, license CC BY-NC-SA 4.0. — [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/piterfm/massive-missile-attacks-on-ukraine)
- Main table `missile_attacks_daily.csv`: `time_start, time_end, model, launch_place, target, target_main, status_data, carrier, launched, destroyed, not_reach_goal…`. It covers massive strikes since October 2022 and is compiled by hand from Ukrainian Air Force and General Staff posts. — [Kaggle description](https://www.kaggle.com/api/v1/datasets/view/piterfm/massive-missile-attacks-on-ukraine)
- **Bias:** the description says the Ukrainian Air Force stopped reporting launched and intercepted counts for some missile types from 10 Aug 2026. When `status_data` = hidden, the counts are unpublished. When only `destroyed` was published, `launched` is set equal to it as a minimum value. — [Kaggle description](https://www.kaggle.com/api/v1/datasets/view/piterfm/massive-missile-attacks-on-ukraine)
- Access: the Kaggle API needs a free account and a token (`kaggle datasets download`). The source data is Ukrainian official reporting only.

**Kaggle "2022 Russia Ukraine War" (losses)** (https://www.kaggle.com/datasets/piterfm/2022-ukraine-russian-war)
- Status: last updated 2026-11-14, version 522, about 206 KB, license CC BY-NC-SA 4.0. Files: `russia_losses_personnel.csv`, `russia_losses_equipment.csv` and `..._correction.csv`. Values are cumulative, so take daily differences (`df.diff()`). The source is the Ukrainian General Staff. — [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/piterfm/2022-ukraine-russian-war)
- A JSON mirror on GitHub is updated daily (last push 2026-11-18) and needs no Kaggle account: https://github.com/PetroIvaniuk/2022-Ukraine-Russia-War-Dataset — [GitHub API](https://api.github.com/repos/PetroIvaniuk/2022-Ukraine-Russia-War-Dataset)
- Bias: these are Ukrainian official claims of enemy losses and are not independently verified.

**ACLED** (https://acleddata.com)
- Needs a myACLED account. The API uses OAuth or cookie authentication, and the old key-based access was being retired (around September 2025 per R package docs). — [ACLED API getting started](https://acleddata.com/api-documentation/getting-started); [access guide](https://acleddata.com/knowledge-base/acled-access-guide)
- The Research tier provides event data with a **12-month delay**. Real-time data is limited to other tiers, for example corporate with a capped number of downloads. — [ACLED access guide](https://acleddata.com/knowledge-base/acled-access-guide); [myACLED FAQ](https://acleddata.com/myacled-faqs)
- Coverage: (background, not verified today) ACLED codes events in both Ukraine and Russia, including "Explosions/Remote violence" events such as drone strikes inside Russia. Its Ukraine Conflict Monitor is a regularly updated product.

**UCDP GED / Candidate** (https://ucdp.uu.se/downloads/)
- The downloads page is live (200). The GED API returned 401 without a token. A mirror of the API spec says it needs a free `x-ucdp-access-token` header, with a quota of about 5,000 requests/day. — [apis.io mirror](https://apis.io/apis/uppsala/uppsala-gedevents-api/); official docs at https://ucdp.uu.se/apidocs/
- (Background) The annual GED release is downloadable as CSV with no token. Monthly "Candidate" events cover the recent period. License CC BY 4.0.

**VIINA (Zhukov)** (https://github.com/zhukovyuri/VIINA)
- Violent-incident data extracted from news articles on the Russian invasion. Verified live, last push 2026-11-16. — [GitHub API](https://api.github.com/repos/zhukovyuri/VIINA)

### Inferences
- With the 12-month ACLED lag, Research-tier users only have data through about November 2025. Students should take the recent period from the Kaggle data, VIINA or GDELT.
- The Kaggle CC BY-NC-SA license fits non-commercial coursework.

### Gaps
- I did not confirm ACLED's current tier names, any student-specific tier, or whether the Ukraine Conflict Monitor data is exempt from the lag.
- I did not confirm the VIINA license or update cadence.

## Q3. Media, political statement, weather and moon-phase drivers

### Takeaway
GDELT 2.0 is live with 15-minute updates and works via raw file download. Each GKG file is about 3.6 MB compressed, so students should filter early and sample date ranges. Open-Meteo's archive API is live and needs no key. For Trump statements there is no fully current open archive I could verify. The best candidates are a Hugging Face dataset last modified October 2025 and UCSB's American Presidency Project.

### Cited Findings
- **GDELT 2.0** is live. `lastupdate.txt` listed files stamped 2026-11-19 07:15 UTC: export about 67 KB, mentions about 82 KB, and GKG about 3.6 MB per 15-minute file (zipped). The site now redirects http to https. — [GDELT lastupdate](https://data.gdeltproject.org/gdeltv2/lastupdate.txt)
- Filtering (background): filter Events on `Actor1/2CountryCode` in (UKR, RUS) or `ActionGeo_CountryCode` = UP or RS, using FIPS codes. Filter GKG on V2Persons containing "donald trump" and V2Locations containing Ukraine. Full history is in BigQuery as `gdelt-bq.gdeltv2.events` and `gkg_partitioned`. That needs a Google Cloud account, and the free query tier (about 1 TB/month, background) can be used up by a single unpartitioned GKG scan. GDELT data is free to use with attribution.
- **Open-Meteo Historical Weather API** verified live: `https://archive-api.open-meteo.com/v1/archive?latitude=..&longitude=..&start_date=..&end_date=..&daily=...` returned 200. (Background: no key needed, free for non-commercial use, CC BY 4.0 data, ERA5-based reanalysis back to 1940, hourly or daily, with fair-use rate limits.) — [Open-Meteo archive endpoint](https://archive-api.open-meteo.com/v1/archive?latitude=50.45&longitude=30.52&start_date=2025-01-01&end_date=2025-01-02&daily=cloud_cover_mean)
- **Moon phase:** the US Naval Observatory API at `https://aa.usno.navy.mil/api/moon/phases/year?year=YYYY` returned 200 (no key). Alternatively, compute it offline with the Python `ephem` or `astral` packages (background), which avoids any API dependency.
- **Trump / Truth Social:**
  - HF dataset `notmooodoo9/TrumpsTruthSocialPosts` is public and not gated, but was last modified 2025-10-23, so it is stale. — [HF API](https://huggingface.co/api/datasets/notmooodoo9/TrumpsTruthSocialPosts)
  - A secondary page reports it at about 5.89 GB, 18,476 Trump posts, CC BY 4.0. It also says the Stiles S3 archive (stilesdata.com/trump-truth-social-archive) stopped updating on 26 Oct 2025. I did not verify these figures. — [search result](https://szulakowski-pl.pages.dev/nightshift)
  - UCSB American Presidency Project lists Truth Social posts by date and is browsable rather than a bulk download. — [UCSB APP](https://www.presidency.ucsb.edu/documents/app-attributes/truth-social?page=6)
  - Academic Truth Social datasets cover all users rather than Trump specifically: 2022 data in [ICWSM 2023](https://ojs.aaai.org/index.php/ICWSM/article/view/22211) and Feb–Oct 2024 data in [arXiv 2411.01330](https://arxiv.org/abs/2411.01330).
- **ISW daily assessments:** understandingwar.org returned 403 to scripted requests, so it was not verifiable. There is no official structured dataset. Students would need to scrape the HTML or PDF reports, and scrapers may be blocked.

### Inferences
- For Trump statements after October 2025, GDELT GKG (with Trump as a person and Ukraine or Russia as themes or locations) is the most practical open proxy.
- For weather, query Open-Meteo once per oblast centroid at daily resolution. That is about 25 locations × 4.7 years, a small number of calls.

### Gaps
- I found no maintained, open, current archive of Trump's Truth Social posts.
- The ISW site's terms and any bot blocking were not checked beyond the 403.

## Q4. Russian MoD intercept claims, strikes on Russian refineries and energy infrastructure, power outages, diplomatic timelines

### Takeaway
None of these has a canonical open dataset. Every option is either an aggregate in news reports, a PDF tracker, a community spreadsheet or GitHub repo, or something students would compile themselves from Telegram posts. Students should plan for manual compilation or a small hand-built event table.

### Cited Findings
- **Russian MoD intercept claims:** I found no open dataset. Totals are tallied from the MoD's daily Telegram briefings. RIA Novosti counted at least 63,993 drones from 1 Jan to end-June 2026, including 14,195 in May, 17,832 in June, and a single-day peak of 1,054 on 17 May. The MoD figures are unaudited. — [United24](https://united24media.com/war-in-ukraine/russia-claims-over-63000-ukrainian-drones-intercepted-in-first-half-of-2026-20341); [Defence Blog](https://defence-blog.com/?p=97750)
- The MoD claimed 4,379 (or about 4,300) drones in December 2025. — [GMA/ABC](https://www.goodmorningamerica.com/news/story/russia-downs-4300-ukrainian-drones-december-setting-new-128800122)
- **Refinery strike trackers:**
  - MNI publishes a periodic PDF tracker of reported Ukrainian drone attacks on Russian refineries since October 2025 and warns that it may not be exhaustive. — [MNI](https://www.mnimarkets.com/articles/mni-ukrainian-drone-strikes-on-russian-refinery-tracker-1765303106068)
  - BBC Verify counted 21 of 38 large refineries hit in 2025 as of October. — [Euromaidan Press](https://euromaidanpress.com/2025/10/03/bbc-verify-counts-21-russian-oil-refineries-hit-since-january-already-48-more-than-in-all-2024/)
  - FT/Rochan counted at least 194 successful strikes in H1 2026, with a record 16 in May. — [United24](https://united24media.com/war-in-ukraine/ukraine-hit-russian-oil-refineries-nearly-200-times-in-first-half-of-2026-20462)
  - A community Google Sheet "Russian Refinery Status Tracker" has no stated maintainer or method. — [Google Sheet](https://docs.google.com/spreadsheets/d/1NfYoI5Qv2XO0I9wDOoJTqe8Y6PRIgESAm3MLQKFUFWA)
  - GitHub repo `brawlerleg/Russian-Fuel-Crisis-2026` was last pushed 2026-07-15. Its content was not reviewed. — [GitHub search](https://api.github.com/search/repositories?q=russian+refinery+strikes)
- **Power outages / energy:** Energy Map (ua-energy.org) hosts Ukrenergo data on planned household stabilization outages (date, hour, outage flag), limited to outages covering more than 50% of regions. Download and license were not confirmed. — [Energy Map resource](https://map.ua-energy.org/en/resources/0f8f9882-1fb2-47c6-81dc-31fbad914f16); [Energy Map](https://ua-energy.org/en/posts/16-12-2024)
- Regional outage schedules are published by distribution companies, not centrally. — [MEV](https://www.mev.gov.ua/en/storinka/why-are-electricity-outage-schedules-introduced-and-what-types-outages-exist)
- Energy-infrastructure strikes can also be filtered from the Kaggle `target` field, ACLED or VIINA (inference).
- **Diplomatic timelines:** there is no structured dataset. Usable curated narrative timelines:
  - [Al Jazeera, Feb 2026](https://www.aljazeera.com/news/2026/2/18/russia-ukraine-talks-all-the-mediation-efforts-and-where-they-stand): Feb 2025 Trump–Putin call; Istanbul talks May–Jul 2025; Anchorage summit Aug 2025; 28→19-point plan Nov 2025; Abu Dhabi and Geneva trilateral rounds Jan–Feb 2026.
  - [Graduate Institute Geneva](https://www.graduateinstitute.ch/communications/news/intense-diplomacy-without-breakthrough-ongoing-peace-efforts-russia-ukraine-war)
  - [The Week/AP, Nov 2026](https://www.theweek.in/wire-updates/international/2026/11/10/past-talks-involving-russia-and-ukraine-have-yielded-little-progress-toward-peace.html)
  - [Obozrevatel 2026 chronicle](https://www.obozrevatel.com/entity/peregovoryi-po-donbassu/) (Russian-language)
  - [TASS factbox](https://tass.com/politics/2087789/amp) (Russian state media, so biased)

### Inferences
- A hand-coded CSV of about 30–60 diplomatic events (date, type, actors, source URL) compiled from the timelines above is the realistic approach. Pair it with a GDELT-derived "diplomacy intensity" series (CAMEO 03x/04x codes) for an automated version.
- Russian MoD and Ukrainian Air Force claims come from opposing belligerents. Use both as noisy indicators rather than ground truth.

### Gaps
- No verified, machine-readable daily MoD intercept series exists. Students must scrape Telegram (t.me/mod_russia) or news tallies.
- I did not verify whether the Energy Map outage data covers 2025–2026 or can be downloaded.
- I did not check Databricks Free Edition's specific outbound internet or storage quotas. (Background: Free Edition is serverless-only with limited compute, so small HTTP/CSV ingestion like Vadimkin, Kaggle, Open-Meteo and sampled GDELT is feasible. Full GDELT GKG history is not.)
