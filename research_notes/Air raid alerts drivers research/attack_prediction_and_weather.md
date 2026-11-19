# Explaining/Predicting Russian Missile & Drone Attacks and Ukrainian Air-Raid Alerts (2022–2026)

## Which papers analyze air-raid alert or missile/drone attack data statistically (time series, forecasting, ML)? Findings?

### Takeaway
Peer-reviewed or preprint literature is thin. The main one is the arXiv preprint by Pavlyshenko & Pavlyshenko (2024): per-oblast Random Forest predicting alert onset. Its strongest signal is lagged alerts in neighbouring regions, and patterns are non-stationary. Most other quantitative work is descriptive tracking by think tanks (CSIS, ISIS, Kyiv Dialogue) plus student or Kaggle-based ML projects.

### Cited Findings
- **Pavlyshenko D., Pavlyshenko B., "Predictive Analytics of Air Alerts in the Russian-Ukrainian War", arXiv:2411.14625 (Nov 2024, cs.LG, preprint, not peer-reviewed).** — [arXiv](https://arxiv.org/abs/2411.14625), [HTML](https://arxiv.org/html/2411.14625v1)
  - Data: Vadym Klymenko's "Air Raid Datasets" (GitHub), turned into a 1-minute binary per-oblast series covering 25 Mar 2022 to 6 Nov 2024.
  - Target: alert starts (or continues for at least 5 more minutes) within 5 minutes. Appendix adds a 15-minute horizon.
  - Features: lagged binary alerts for all regions, current cumulative alert duration, hour, day of week, month, and `ndays` (days since start).
  - Model: scikit-learn RandomForest (500 trees), one model per oblast (Lviv, Vinnytsia, Kyiv, Kharkiv). Time split at 2024-07-01. Evaluated with ROC/AUC and confusion matrices.
  - Numeric AUC values appear only in the figures. Some figures are mislabelled, e.g. the Kharkiv figures reuse the Kyiv images.
  - Findings: neighbouring-region features are the most important. Neighbours of Kharkiv correlate more with Kharkiv than western oblasts do. `ndays` is important for some regions, meaning alert patterns drift and the model needs retraining.
  - Caveat: the abstract says it forecasts "duration", but the model is actually an onset classifier.
- **Hukovych B., Yoo H., Žídeková L., "Predicting Missile and Drone Destruction: A Data-Driven Approach Using ML" (student project, ~Feb 2025, not peer-reviewed).** — [PDF](https://hukovychb.github.io/media/docs/Predicting-Missile-and-Drone-Destruction.pdf)
  - Data: Kaggle "Massive Missile Attacks on Ukraine" (piterfm; records of launched and destroyed counts by weapon type and launch place) merged with Meteostat daily weather for Kyiv station 33345 (temperature, wind, precipitation).
  - Models: OLS, Elastic Net, RF, XGBoost, MLP, kNN, SVR, and ensembles.
  - Findings: "weather conditions have a minimal impact on interception success". Launch volume is the significant predictor of the number destroyed. Ensembles perform best.
  - The authors acknowledge that one Kyiv station is a crude weather proxy.
- **Kaggle dataset "Massive Missile Attacks on Ukraine" (uploader piterfm)**: a widely reused attack-level table built from Ukrainian Air Force reports. — [Kaggle](https://www.kaggle.com/datasets/piterfm/massive-missile-attacks-on-ukraine) (referenced in the Hukovych et al. PDF)
- **Safety & Defense (sd-magazine.eu) article, Dec 2025**: analyzes meteorological conditions around Shahed attacks. Details are in the weather section below. — [sd-magazine.eu](https://sd-magazine.eu/index.php/sd/article/download/272/197/) (the server refused connections; content known only from search snippets)
- **CSIS "Drone Saturation: Russia's Shahed Campaign"**: descriptive analysis of Ukrainian Air Force data with no statistical testing. — [CSIS](https://www.csis.org/analysis/drone-saturation-russias-shahed-campaign)
  - ~130 launches/week before Sep 2024, rising to a ~1,100/week peak. The text also cites ~200 rising to >1,000/week by Mar 2025, so the baseline is internally inconsistent.
  - Launch-site counts: Primorsko-Akhtarsk 312, Kursk 248, Chauda 160, Oryol 130, Bryansk 113, Millerovo 100, Yeysk 37.
- **ISIS (Institute for Science and International Security) monthly "Analysis of Russian Shahed-type UAV Deployment"**: built from daily Air Force reports. ISIS calls its figures a "published-source baseline", not official 24h totals. — [ISIS](https://isis-online.org/isis-reports/monthly-analysis-of-russian-shahed-136-deployment-against-ukraine-updated)
  - Example report (Sep 2026). — [PDF](https://isis-online.org/uploads/isis-reports/documents/September_2026-Updated-Analysis-of-Russian-Shahed-type-UAVs-Deployment-Against-Ukraine.pdf)
- **Kyiv Dialogue "Ukraine Air War Monitor" (Vol. XV)**: database of ~91,700 documented attacks over 43+ months, built from Air Force reports and cross-checked with ISW and OSINT. Reports 1.6% deviation from CSIS. — [Kyiv Dialogue](https://www.kyiv-dialogue.org/en/news/newsreader/ukraine-air-war-monitor-vol-xv.html)
  - March 2026 totals: 6,603 aerial weapons, of which 6,462 were drones (63% Shahed/Gerbera, the rest decoys) and 141 were missiles.
  - Interception rates: drones 90%, cruise missiles 89%, ballistic missiles ~35%.
  - Record wave: 982 drones and missiles within 24h on 23/24 Mar 2026 (previous record 823 on 7 Sep 2025).
- **Data caveat (Kyiv Post)**: Air Force reports often cover only the 18:00–08:00 window, so official daily figures under-count daytime launches. — [Kyiv Post](https://www.kyivpost.com/analysis/83498)
- **Other datasets**:
  - BlackSeaNews monthly database of launches from occupied Crimea. — [BlackSeaNews](https://www.blackseanews.net/en/read/229484)
  - Missile Defense Advocacy "Ukrainian War Tracker" (from Jan 2025). — [MDAA](https://missiledefenseadvocacy.org/?p=39307)
  - GitHub "missile-attack-watcher". — [GitHub](https://github.com/pavelsivanovs/missile-attack-watcher)

### Inferences
- The likely strongest short-horizon predictor of an alert in oblast X is the current alert state of its neighbours, i.e. spatial propagation of a raid. Calendar features are secondary.
- Patterns drift: rolling or online retraining and time-based splits are necessary.
- No public study yet combines alert time series with attack counts and weather in one model. That leaves a clear gap for a project.

### Gaps
- I found no Texty, Ukrainska Pravda or KSE statistical (as opposed to descriptive) study of alert time series. Google Scholar and SSRN were not searched exhaustively.
- I found no published AUC or benchmark numbers in text form for alert forecasting.
- I did not read any Kaggle notebooks individually.

## What evidence exists that weather/moon/season affect Shahed or missile launch timing and size?

### Takeaway
There is good evidence that weather (low cloud, rain, fog, snow) degrades Ukrainian *interception*, especially the visual mobile fire groups and interceptor drones. One 2025 study claims the largest Shahed raids cluster under temperature-inversion conditions. Whether Russia deliberately *times* raids to weather is contested. I found no evidence at all on moon phase.

### Cited Findings
- **SD-Magazine (Safety & Defense) Dec 2025 study**: hypothesizes that Russia times mass Shahed strikes to weather, using cloud base and total cloud cover among its variables. — [sd-magazine.eu](https://sd-magazine.eu/index.php/sd/article/download/272/197/)
  - Reported (via search snippet): of strikes with >100 UAS, 78% occurred under inversion conditions, and all 39 strikes with >200 UAS took place during inversions.
  - Reliability: full text not verified. The journal is a small open-access outlet.
- **Zelensky (10 Oct 2025, via Reuters)**: overcast weather cut air-defense effectiveness by "20–30%". — [Kyiv Independent, 13 Oct 2025](https://kyivindependent.com/ukraines-autumn-rains-help-shahed-type-drones-evade-ukrainian-air-defense)
- **Same Kyiv Independent article, Kyiv Oblast mobile air-defense coordinator**: a scope sees ~100–200 m in rain or snow versus ~2,000 m normally. "Shaheds fly in any weather." — [Kyiv Independent](https://kyivindependent.com/ukraines-autumn-rains-help-shahed-type-drones-evade-ukrainian-air-defense)
- **Same article, aviation expert Khrapchynskyi**: low cloud, rain, snow and fog hinder acquisition even with thermal imaging. — [Kyiv Independent](https://kyivindependent.com/ukraines-autumn-rains-help-shahed-type-drones-evade-ukrainian-air-defense)
- **Interceptor drones are weather-limited**: a commander says they are effective only in good weather, "not in -20°, not in snow, not in rain". Syrsky says SAMs are the all-weather backbone. — [Kyiv Independent](https://kyivindependent.com/winter-has-grounded-ukraines-interceptor-drones-gutting-kyivs-air-defense)
- **Air Force spokesman Ihnat, two positions**:
  - High cloud hinders aiming, and Russia exploits weather and "dark hours". — [TSN](https://tsn.ua/en/ato/russian-attacks-on-ukraine-ignat-explained-how-the-enemy-is-exploiting-weather-whims-2370307.html)
  - In other remarks he says weather "doesn't have much impact" because drones fly pre-set routes. This is a contradiction within official messaging. — [mind.ua](https://mind.ua/en/news/20259931-occupiers-use-poor-weather-for-air-attacks-on-ukraine)
- **13 Sep 2026, 863-drone wave**: CyberBoroshno-tracked routes ran almost entirely under cloud over northern and western Ukraine, forcing mobile teams to hunt by sound. — [MigFlug](https://migflug.com/afterburner/russia-863-drone-barrage-ukraine-cloud-cover-geran-2026/); [Defence Blog](https://defence-blog.com/?p=100996)
  - Reliability: medium (secondary aviation blogs relaying Telegram OSINT).
- **Season (UK Defence Intelligence)**: weather likely reduced Shahed launches in December (2023). RBC-Ukraine's expert put the chance that weather caused a pause at 70–80%. This suggests icing or storms can *suppress* launches. — [Ukranews](https://ukranews.com/en/news/1054571-british-intelligence-explains-why-russia-launches-fewer-shahed-drones-over-ukraine-in-december); [RBC-Ukraine](https://newsukraine.rbc.ua/news/night-without-shaheds-why-russia-pauses-uav-1733836876.html)
- **Sea approaches**: waves plus bad weather mask engine noise on Odesa routes. — [Kyiv Post](https://kyivpost.com/post/27206)
- **ML study**: daily Kyiv weather had "minimal impact" on interception success in 2022–2023 data. This partially contradicts the anecdotal accounts, though it uses a coarse weather proxy. — [Hukovych et al.](https://hukovychb.github.io/media/docs/Predicting-Missile-and-Drone-Destruction.pdf)
- **Moon phase**: no source found linking lunar illumination to launch timing or size. The closest is Ihnat's statement that Russia uses darkness, i.e. most raids are overnight. — [TSN](https://tsn.ua/en/ato/russian-attacks-on-ukraine-ignat-explained-how-the-enemy-is-exploiting-weather-whims-2370307.html)
- **Shift toward daytime attacks (2025–26)**: intensive attacks increasingly continue into the following day. — [CUAS Hub](https://cuashub.com/en/content/russian-tactics-shift-to-daytime-drone-strikes/); [RBC-Ukraine](https://newsukraine.rbc.ua/analytics/hundreds-of-drones-every-night-how-russia-1741338740.html)

### Inferences
- Weather probably matters more for *penetration and outcomes* than for *launch decisions*. Severe weather (icing, storms) may suppress launches, while moderate overcast may favour large raids. The SD-Magazine inversion result, if robust, points to atmospheric stability or cloud as a feature worth testing.
- The weather proxy should be route- or region-specific (e.g. ERA5 or Open-Meteo per oblast) rather than a single station.
- Moon phase is untested and so a novel hypothesis. Its effect may be weak, given thermal optics and the move to daytime attacks.

### Gaps
- The full SD-Magazine methodology could not be retrieved (connection refused).
- No study quantifies a wind effect on Shahed launch timing.
- No quantitative season-of-year decomposition of launches was found.

## Are there documented periodicities (e.g., massive strikes every N days, accumulation before waves)?

### Takeaway
CSIS documents an average of 8.2 days between major salvos in 2025, with intervals compressing to ~2 days at times and stretching to 38 days during diplomatic talks. ISW and CSIS repeatedly describe accumulating stockpiles before massive combined strikes. Shahed launches themselves are near-continuous. Diplomacy and production cycles are better explanations than a fixed period.

### Cited Findings
- **CSIS "Russia's Massed Strikes: Coercion by Salvo" (Russian Firepower Strike Tracker)**: — [CSIS](https://www.csis.org/analysis/russias-massed-strikes-strategy-coercion-salvo)
  - Salvos are ~10% of Russian aerial operations.
  - Average salvo size: ~100 weapons roughly monthly in 2022, ~370 in 2025.
  - Average gap between major salvos in 2025: 8.2 days. The gap reached 38 days in August, when Russia avoided salvos over 300 during talks.
  - Pauses are described as letting Russia rebuild inventory. This is an inference, with no inventory data shown.
- **CSIS "The New Salvo War"**: intervals between major strikes compressed from roughly a month to as few as two days. — [CSIS](https://www.csis.org/analysis/new-salvo-war)
- **CSIS "Drone Saturation"**: in 7 months there was no three-day stretch without Shahed launches. 75% of launches fell on consecutive days, and salvos came nearly every other day. — [CSIS](https://www.csis.org/analysis/drone-saturation-russias-shahed-campaign)
- **ISIS**: Shahed launches show "cyclical patterns", with spikes followed by short lulls. — [ISIS](https://isis-online.org/isis-reports/monthly-analysis-of-russian-shahed-136-deployment-against-ukraine-updated)
- **ISW**:
  - Russia likely stockpiled ballistic and cruise missiles through September 2025 to strike on select days. — [Ukrinform/ISW](https://www.ukrinform.net/rubric-ato/4043752-russia-stockpiled-missiles-in-september-for-new-largescale-strikes-on-ukraine-isw.html)
  - After 29 Dec 2023, Russia was unable to sustain repeated large-scale missile strikes, whereas drone strikes can be more consistent. — [Ukrinform/ISW](https://www.ukrinform.net/rubric-ato/3806819-russia-unable-to-sustain-repeated-largescale-missile-strikes-against-ukraine-isw.html)
  - In June 2026, the reduced frequency of massive strikes may reflect production limits. — [Ukranews/ISW](https://ukranews.com/en/news/1161006-russia-sharply-reduces-its-massive-strikes-on-ukraine-isw-outlines-two-possible-scenarios?print=1)
- **Frequency counts**: ~20 nights/month with >100 drones and ~5 with >200 (2025). — [Ukrainian Week](https://ukrainianweek.com/russian-shaheds/)
  - Kyiv Dialogue counts 21, 24 and 27 attacks with >100 drones in Jan, Feb and Mar 2026. — [Kyiv Dialogue](https://www.kyiv-dialogue.org/en/news/newsreader/ukraine-air-war-monitor-vol-xv.html)
- **Pauses**:
  - First Shahed-free night after 112 consecutive days (Apr 2025). — [NV](https://english.nv.ua/nation/russia-pauses-shahed-drone-attacks-after-112-days-in-row-50502462.html)
  - First drone-free night in 48 days. — [United24](https://united24media.com/latest-news/ukraine-marks-first-night-without-shahed-drone-attacks-in-48-days-2980)
- **Lower-than-usual drone counts as a precursor**: Ukrainian observers treat a quiet night as a warning sign of an upcoming massive strike. Descriptive journalism, not a test. — [Euromaidan Press, Apr 2026](https://euromaidanpress.com/2026/04/05/fewer-russian-drones-last-night-thats-when-ukraine-starts-watching-the-skies-more-carefully)
- **Defense News (Aug 2026)**: Ukraine braces for combined salvos of up to 200 missiles. — [Defense News](https://defensenews.com/global/europe/2026/08/20/ukraine-braces-for-combined-salvos-of-up-to-200-missiles-as-overnight-attack-kills-15-in-kyiv)

### Inferences
- Useful features include days since the last massive (missile) salvo and a rolling 7-day drone count, where a dip suggests accumulation. Political-event flags (talks, summits) also matter.
- Missile salvos behave like a renewal process limited by production, while drones behave like a near-daily baseline with spikes.

### Gaps
- No formal spectral or autocorrelation analysis of launch series was found.
- No rigorous day-of-week study was found. Anecdotally, large strikes are often claimed on weekends or holidays, but this is unverified.

## Any studies on alert duration, regional spread, or prediction of massive attacks?

### Takeaway
Alert-duration work is mostly descriptive: regional totals and shares of business or working hours, from Ukrainian media and business groups. Regional spread is addressed only by the arXiv correlation and feature-importance findings. I found no published model predicting *massive* attacks.

### Cited Findings
- **alerts.in.ua**: ~14,870 alarms in Ukraine in 2022, compiled from local media, Suspilne, regional administrations and apps. — [Babel](https://babel.ua/en/news/88907-in-ukraine-the-number-of-air-alarms-per-year-was-calculated)
- **Kyiv Post analysis**: about 40 sirens per day nationally. — [Kyiv Post](https://www.kyivpost.com/amp/post/18257)
- **Dengi.ua**: secondary source with an unclear underlying study. — [Dengi.ua](https://dengi.ua/en/business/9761391-air-raid-alerts-downtime-and-business-losses-in-ukraine)
  - Sumy: share of working hours under alert rose from 11% (2023) to 72% (H1 2026).
  - Kharkiv vs Lviv alert duration: 6x (2023) widening to 40x (2026).
- **Q1 2026 (1 Jan to 24 Mar) totals, air-alarms.in.ua via slovoidilo**: Dnipropetrovsk 1,780h, Donetsk 1,711h, Kharkiv 1,609h, Sumy 1,527h. — [Interfax-Ukraine](https://en.interfax.com.ua/news/general/1164632.html)
- **Ukrainian Council of Shopping Centers**:
  - Alerts were active during a record 30.8% of mall opening hours in Sep 2026. — [Ukrainska Pravda](https://www.pravda.com.ua/eng/news/2026/10/05/8056546/)
  - Monthly series since 2022 and an interactive regional map. — [UCSC](https://ucsc.org.ua/?p=45096); [UP Feb 2025](https://www.pravda.com.ua/eng/news/2025/02/04/7496741/)
- **Texty.org.ua "How air raid alerts are paralyzing Kyiv"**: 46 Kyiv alerts in 27–30 Aug 2026. — [Texty](https://texty.org.ua/articles/118269/how-air-raid-alerts-are-paralyzing-kyiv/)
  - Record day 27 Aug: 14 hours (~60% of the day).
  - Argues fragmentation (number of interruptions) matters as much as total duration.
  - The data source is not stated.
- **Regional frequency breakdown**. — [FAIR](https://www.fair.org.ua/en/v-iakykh-oblastiakh-povitriana-tryvoha-lunaie-naichastishe-povnyi-hid-po-rehionakh-ukrainy/)
- **Spatial structure**: lagged neighbour alerts dominate feature importance in the RF onset model. — [arXiv 2411.14625](https://arxiv.org/html/2411.14625v1)
- **Alerts API**: real-time and historical data. — [alerts.in.ua API](https://api.alerts.in.ua/v3/alerts/active.md)

### Inferences
- Front-line oblasts (Kharkiv, Sumy, Dnipropetrovsk, Donetsk) are dominated by near-continuous alerts driven by KABs (glide bombs) and tactical threats. Western oblasts' alerts are driven mainly by long-range raids. Models should be split by regime.
- Since Aug 2025 the share of time under alert has risen sharply, a structural break to handle in modelling.

### Gaps
- No academic survival or duration model of alerts was found.
- No massive-strike early-warning model was found. Ukrainian monitoring channels' informal indicators (Tu-95 movements to Olenya/Engels, ship departures) have not been studied quantitatively in open literature.
- KSE and SSRN were not directly confirmed to have relevant papers.
