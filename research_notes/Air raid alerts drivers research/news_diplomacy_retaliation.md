# News, Diplomacy, Retaliation and Strike Intensity in the Russia–Ukraine War (2022–2026) + Conflict-Forecasting Methods

## Q1. Is there quantitative evidence that diplomatic events (talks, summits, Trump statements, aid decisions, ultimatums) predict Russian massive strikes? Lags and effect sizes?

### Takeaway
I found no peer-reviewed study that formally estimates lags or effect sizes between diplomatic events and Russian strike volumes. The best quantitative evidence is descriptive. CSIS Futures Lab's salvo tracking points to calibration: fewer large salvos during an active negotiation window (August 2025), then a rebound. Separately, many record attacks fall within ±1 day of Trump–Putin contacts or deadlines (May–July 2025). The two patterns pull in opposite directions, so the dependency is regime-specific, not a stable sign.

### Cited Findings
- CSIS Futures Lab (Jensen & Atalan, 9 Sep 2025), drawing on its Russian Firepower Strike Tracker:
  - Russia launched >6,300 UAVs and missiles in July 2025, but only ~3,300 in August 2025, during negotiations with Trump (Alaska summit period).
  - In August the gap between major salvos was 38 days, against a 2025 average of 8.2 days, and Russia avoided salvos of >300 munitions during the talks.
  - Large-scale operations resumed afterwards, culminating in the 7–8 Sep 2025 attack of >800 munitions.
  - CSIS reads this as Moscow "calibrating" scale and tempo to the political environment. It publishes no statistical test. — [CSIS, Russia's Massed Strikes: Coercion by Salvo](https://www.csis.org/analysis/russias-massed-strikes-strategy-coercion-salvo)
- Salvo trend from the same CSIS piece: about 100 weapons per salvo roughly monthly in 2022, against ~370 munitions per salvo about every 8 days in 2025, with intervals sometimes as short as 2 days. Large salvos are about 10% of Russian aerial operations. Combined interception is ~85%, and Shahed hit rates rose from <10% to ~20%. — [CSIS](https://www.csis.org/analysis/russias-massed-strikes-strategy-coercion-salvo)
- Records clustered around Trump–Putin contacts:
  - 18 May 2025: a then-record 273 drones, one day before a planned Trump–Putin call. — [Kyiv Independent](https://kyivindependent.com/russia-launches-record-273-drone-attack-on-ukraine-ahead-of-planned-trump-putin-call/)
  - After Trump's "two weeks" timeframe of 28 May 2025, the record was broken on 1 Jun (472 drones) and 9 Jun (479 drones + 20 missiles). — [Yahoo/aggregated report](https://www.yahoo.com/news/trump-gave-putin-two-week-122700521.html)
  - 3–4 Jul 2025: a record of ~550 drones and missiles, mostly at Kyiv, hours after Trump said a call with Putin made "no progress". — [CNN](https://www.cnn.com/2025/07/03/europe/kyiv-ukraine-strikes-trump-putin-talks-intl-hnk); [Bloomberg](https://www.bloomberg.com/news/articles/2025-07-03/kremlin-signals-putin-trump-call-made-little-progress-on-ukraine)
  - In July 2025 Trump cut his 50-day sanctions deadline to 10–12 days after Russian attacks. This is a reverse link, where strikes drive diplomatic statements, which is an endogeneity issue for modelling. — [Fox News](https://www.foxnews.com/world/trump-disappointed-putin-says-hell-reduce-50-day-deadline)
- Centre for Information Resilience (CIR): in H1 2025 it verified ≥945 civilian-harm incidents, among the highest levels since 2022, with strikes continuing through major peace-talk milestones. This is descriptive and not a timing test. — [CIR](https://www.info-res.org/eyes-on-russia/articles/record-breaking-russian-strikes-during-peace-negotiations/)
- UNITED24 Media keeps an advocacy-leaning timeline of "strikes after talks" since 2014, for example a ballistic attack during the Abu Dhabi talks on 24 Jan 2026. It is useful as an event list but is not systematic. — [UNITED24](https://united24media.com/war-in-ukraine/when-peace-talks-begin-russia-bombs-a-pattern-timeline-15165)
- Forbes (18 Nov 2026) says Russia keeps up mass missile and drone strikes despite ongoing peace discussions, for example 17 ballistic + 59 cruise missiles on 2 Nov 2026. It links this to a stalled ground offensive and an expanding missile production base. — [Forbes](https://www.forbes.com/sites/vikrammittal/2026/11/18/russia-expands-missile-arsenal-to-sustain-strikes-against-ukraine/)
- The Ternopil strike (19 Nov 2025) came while Zelensky was trying to restart talks. Russia framed it as retaliation. — [Wikipedia: 2025 Ternopil strike](https://en.wikipedia.org/wiki/2025_Ternopil_strike)
- Main open data for building such tests:
  - Petro Ivaniuk's Kaggle "Massive Missile Attacks on Ukraine" (since Oct 2022), compiled manually from Ukrainian Air Force and General Staff reports. — [Kaggle](https://www.kaggle.com/datasets/piterfm/massive-missile-attacks-on-ukraine)
  - CSIS used this dataset for its tracker, covering 27 Sep 2022–30 Nov 2024 in its first release. — [CSIS tracker](https://www.csis.org/programs/futures-lab/projects/russian-firepower-strike-tracker-analyzing-missile-attacks-ukraine); [CSIS assessment](https://www.csis.org/analysis/assessing-russian-firepower-strikes-ukraine)
  - Data caveat: a Kaggle note reports that the Ukrainian Air Force stopped reporting some missile launch/interception counts from 10 Aug 2026. This is a structural break in the series. — [Kaggle data page](https://www.kaggle.com/datasets/piterfm/massive-missile-attacks-on-ukraine/versions/98/data)

### Inferences
- Two competing mechanisms show up in the anecdotal record:
  - **Coercive signalling**: spikes just before or after calls, deadlines and talks, to raise leverage or show defiance.
  - **Restraint during high-stakes windows**: the August 2025 lull before the Alaska summit.
  A model should therefore use event-type-specific dummies (call, summit, ultimatum or deadline, sanctions or aid announcement) with leads and lags of roughly −3 to +7 days, rather than one "diplomacy" variable.
- Salvo timing is also driven by stockpile accumulation. CSIS's inter-salvo interval of ~8 days suggests a supply- or production-driven cycle. Any diplomacy effect must be tested against a baseline that controls for time since the last salvo, for example a renewal or Hawkes-type baseline. Otherwise coincidences with frequent diplomatic events (calls happen weekly) will look significant.
- Selection bias: media timelines highlight strikes that coincide with talks. With diplomatic events dense in 2025, random overlap is likely. Permutation or placebo-date tests are needed.

### Gaps
- No peer-reviewed or preprint event study or Granger test linking Ukraine-war diplomatic events to strike counts was found, including on arXiv and Google Scholar-type queries. Lags and effect sizes are therefore unavailable.
- CSIS gives no methodology or significance tests for the "calibration" claim. Its tables and figures were not retrievable.
- I found no systematic evidence on US aid decisions (for example the PDA pauses in 2025) and strike volumes.
- Post-Alaska and 2026 dynamics are covered only by journalism.

## Q2. Evidence on reciprocity and retaliation in strike exchanges (Ukrainian long-range strikes vs Russian massive attacks)

### Takeaway
Both sides explicitly frame their energy and long-range strikes as retaliation ("mirror response"). Episode-level evidence exists for Operation Spiderweb, where Putin told Trump he "will have to respond" and record drone attacks followed within days. However, no quantitative study of reciprocity (Granger, VAR or Hawkes cross-excitation) for this war was found. Ukrainian refinery strikes escalated sharply in 2025–2026, which gives a usable "treatment" series.

### Cited Findings
- **Spiderweb (1 Jun 2025):**
  - In a 75-minute call on 4 Jun 2025, Putin told Trump he would respond to Operation Spiderweb. — [Axios](https://www.axios.com/2025/06/04/putin-trump-call-ceasefire-drone-attack); [Euromaidan Press](https://euromaidanpress.com/2025/06/04/putin-tells-trump-in-phone-call-he-will-retaliate-recent-spiderweb-drone-operation-on-russian-airfields/); [Ukrinform](https://www.ukrinform.net/rubric-polytics/4000727-putin-tells-trump-he-will-have-to-respond-to-ukraines-operation-spiderweb.html)
  - Analysts (via CNN) saw the initial retaliation in a massive drone and missile strike on the night of 5–6 Jun. Russia's MoD later claimed a strike on an airfield in Rivne. — [Yahoo/CNN](https://www.yahoo.com/news/putin-promised-ukraine-pay-airbase-145404460.html)
  - Confounder: a record 472 drones on 31 May/1 Jun came the day *before* Spiderweb, so the escalation trend was already under way. — same source
  - Trump predicted Russia's response would "not be pretty". — [Kyiv Independent](https://kyivindependent.com/russias-response-to-operation-spiderweb-is-likely-not-going-to-be-pretty-trump-says/amp)
  - Some analysts argued a dramatic response would implicitly admit the damage. — [Yahoo/CNN](https://www.yahoo.com/news/putin-promised-ukraine-pay-airbase-145404460.html)
- **Energy-for-energy spiral:**
  - Ukraine largely paused energy strikes in spring and early summer 2025, then resumed them after Russia renewed attacks on Ukraine's grid. Putin in turn framed Russian strikes as a response. — [Spokesman-Review](https://www.spokesman.com/stories/2025/sep/22/as-russia-pummels-ukraines-energy-kyiv-hits-back-a); [Chatham House](https://www.chathamhouse.org/2025/11/ukraines-best-defence-against-putins-energy-war-more-attacks-russias-oil-refining-sector)
  - Putin called retaliation a "mirror" response. Zelensky offered to stop refinery strikes if Russia stopped hitting Ukraine's energy. Russia rejected a Black Sea shipping-for-refineries swap. — [Geopolitical Monitor](https://www.geopoliticalmonitor.com/ukraine-refinery-strikes-russia/)
- **Scale of Ukrainian strikes (treatment intensity):**
  - Bloomberg counted 120 attacks on Russian energy facilities in 2025, 81 of them on refineries. — [Ukrainska Pravda](https://www.pravda.com.ua/eng/news/2025/12/31/8014117)
  - Insurers estimate Russian oil-sector losses at >1 trillion RUB (~$12.9bn) in 2025. — [Moscow Times](https://www.themoscowtimes.com/2026/02/09/ukrainian-strikes-cost-russian-oil-sector-over-13bln-in-2025-insurers-say-a91894/pdf)
  - Reuters sources say drone attacks have cut Russian refinery throughput by ~45% since late October 2026, with 15 of 35 major refineries disrupted. Other estimates differ (~30%, or Zelensky's ">55%"). — [US News/Reuters](https://www.usnews.com/news/world/articles/2026-11-18/exclusive-drone-attacks-nearly-halve-russias-november-oil-refining-sources-say); [NV](https://english.nv.ua/nation/thirteen-day-drone-blitz-paralyzes-36-of-moscow-s-oil-50658616.html)
  - Russia claimed one Ukrainian attack involved >1,300 drones. — [CBC](https://www.cbc.ca/news/world/ukraine-russia-drone-attacks-9.7423256)
- **Russian strikes on Ukraine's energy:** 27 documented strikes in 2023, 94 in 2024 and 142 in 2025, attributed to Russia Matters' OSINT. These figures are relayed via a Substack, so verify them. — [Substack](https://thechrissampson.substack.com/p/burning-the-lifeline-how-ukraine)
- **Methodological precedents on reciprocity:**
  - Goldstein & Pevehouse (1997, APSR, Bosnia) used VARs and found both reciprocal and "inverse" responses. For example, Serb forces cooperated after NATO punishment. — [RePEc](https://econpapers.repec.org/RePEc:cup:apsrev:v:91:y:1997:i:03:p:515-529_21)
  - Linke, Witmer & O'Loughlin (2012, International Interactions) applied space-time Granger tests to the Iraq WikiLeaks logs. They found strong tit-for-tat between coalition forces and insurgents, varying by ethnicity, urbanisation and income. — [RePEc](https://econpapers.repec.org/RePEc:taf:ginixx:v:38:y:2012:i:4:p:402-425)
  - Jaeger & Paserman (AER 2008, Second Intifada) found unidirectional Granger causality from Palestinian to Israeli violence, and no tit-for-tat in the other direction. — [IZA DP 1808](https://iza.org/publications/dp/1808)
  - Asali, Abu-Qarn & Beenstock argue that linear VARs on zero-inflated counts are biased and propose nonlinear VARs. — [Toronto seminar paper](https://www.economics.utoronto.ca/index.php/index/research/downloadSeminarFile/14598)

### Inferences
- Rhetorical retaliation is common on both sides, but the observed timing is confounded:
  - Russia was already escalating (records on 18 May and 1 Jun) before Spiderweb.
  - Production and stockpile cycles and weather drive salvos regardless of Ukrainian actions.
  A multivariate Hawkes model (Ukraine→Russia cross-excitation kernel) or a count-VAR with salvo-interval controls is the proper test. Literature precedents show results depend on specification (linear vs nonlinear, daily vs weekly aggregation).
- Ukrainian deep strikes appear less tied to diplomatic calendars and more to targeting campaigns. The reverse direction (Russian massed strikes → Ukrainian refinery strikes) is just as plausible and should be tested in both directions.

### Gaps
- No quantitative reciprocity study of Russia–Ukraine long-range exchanges was found.
- No ISW or Carnegie piece specifically analysing retaliation timing was retrieved, despite searches.
- There is no consolidated, open daily dataset of Ukrainian strikes inside Russia. Russian MoD "drones downed" claims are a possible but biased proxy.

## Q3. Standard and recommended conflict-forecasting methods (news/events data, Hawkes, event studies, Granger), and known pitfalls

### Takeaway
State of the art (ViEWS) uses probabilistic forecasts of fatality counts, evaluated with CRPS, ignorance score and interval scores against strong baselines. News text (topic models) adds early-warning signal, especially for rare onsets. Hawkes and self-exciting processes are a standard tool for "violence begets violence" and retaliation, but self-excitation estimates are model-sensitive. Key pitfalls:
- reporting and media-attention bias
- language and coverage bias in GDELT
- duplicate reports
- reporting delays (ACLED backfill)
- endogeneity: violence drives news and diplomacy
- non-stationary baselines

### Cited Findings
- **ViEWS 2023/24 Prediction Challenge** (Hegre et al.): the task is to predict country-month battle-related deaths *with uncertainty*. Forecasts are scored by CRPS, ignorance score (IGN) and Mean Interval Score (MIS), with bootstrapped evaluation windows. The 2024/25 round is a live, real-time challenge. — [arXiv 2407.11045](https://arxiv.org/abs/2407.11045v1); [PRIO project](https://www.prio.org/projects/2002)
  - A participant's transformer model beat benchmarks on CRPS and MIS, but not on IGN, where the "Conflictology" benchmark won. Simple history-based baselines are hard to beat. — [Univ. Turin paper](https://iris.unito.it/retrieve/5ed4bce3-33ee-4293-88ba-2c8719d1f313/Unito_VIEWSPredictionChallenge2023.pdf)
  - Observed Markov models were proposed for fatality densities. — [arXiv 2410.12374](https://arxiv.org/pdf/2410.12374)
  - Dynamic elastic net was used for forecasting changes in fatalities in the earlier ViEWS competition. — [arXiv 2205.14073](https://arxiv.org/pdf/2205.14073)
- **News text for forecasting:** Mueller & Rauh, "The Hard Problem of Prediction for Conflict Prevention" (JEEA 2022), apply LDA to 4.1M newspaper articles and feed the topics into a random forest. Text helps most with the hard problem of onsets in previously peaceful places. — [BSE](https://bse.eu/research/publications/hard-problem-prediction-conflict-prevention); [CEPR DP13748](https://repec.cepr.org/repec/cpr/ceprdp/DP13748.pdf)
- **GDELT added to ViEWS:** GDELT added to the 653 ViEWS covariates came "at no cost to accuracy" but did not markedly improve forecasts. The authors de-duplicated events covered by multiple outlets. — [arXiv 2106.00306](https://arxiv.org/pdf/2106.00306) (identified via search snippet; verify exact attribution)
- **Hawkes / self-exciting processes:**
  - Lewis, Mohler, Brantingham & Bertozzi used Iraq Body Count data (2003–07). Self-exciting models beat a Poisson baseline, the background rate is non-stationary and shifts with conflict phases, and the mechanism is reprisal and counter-reprisal cycles. — [UCLA PDF](https://www.math.ucla.edu/~bertozzi/papers/iraq.pdf)
  - Dyadic (actor-pair) Hawkes models for Afghanistan capture counter-attacks by allies; 36.3% of events lack actor-pair information. — [Georgia Tech PDF](https://faculty.cc.gatech.edu/~zha/papers/km0600s-li-1.pdf)
  - Clark & Dixon (Iraq terrorism) found that conclusions about whether self-excitation exists depend on the process model chosen. — [arXiv 1703.08429](https://ar5iv.arxiv.org/html/1703.08429)
  - Browning et al. (2024) fit a Bayesian spatiotemporal discrete-time Hawkes model to ACLED (South Asia). It suits daily or weekly binned counts such as air-alert or strike days. — [arXiv 2408.14940](https://arxiv.org/abs/2408.14940v1)
- **Granger and VAR on event data:**
  - Goldstein's WEIS-based VARs (12 Middle East dyads) found bilateral reciprocity widespread, but it did not predict long-term shifts. — [Colorado PDF](https://ibs-lb.colorado.edu/johno/pub/II_2.pdf)
  - Kang & Reuveny (JPR 1998) found reciprocal Granger causality between trade and conflict, which implies simultaneity and endogeneity. — [JPR DOI page](https://https-sage-cnpereading-com-443.webvpn1.xju.edu.cn/doi/10.1177/0022343398035005003)
  - See also the Q2 precedents: Linke et al. 2012 and Jaeger & Paserman 2008.
- **Reporting bias:**
  - Weidmann (AJPS 2016) compared media-based events with Afghan military records. Cellphone coverage predicts *reporting*, which inflates the apparent effects. Event severity reduces reporting bias, which gives a diagnostic test. — [AJPS blog](https://ajps.org/2015/07/27/a-closer-look-at-reporting-bias-in-conflict-event-data/); [IDEAS](https://ideas.repec.org/a/wly/amposc/v60y2016i1p206-218.html)
  - A rebuttal found the effects are not wholly an artifact. — [Research & Politics 2017](https://doaj.org/article/541c20adfaa44713a00a415d16242d46)
- **Reporting delays:** treating the latest ACLED counts as complete underestimates uncertainty in real-time forecasts. — [arXiv 2603.25964](https://arxiv.org/pdf/2603.25964)
- **Language and media-attention bias:** GDELT mainly indexes English-language outlets, so local-language reporting is underrepresented. Events in low-media-access areas are under-coded in ACLED. — [arXiv 2607.00018](https://arxiv.org/html/2607.00018)
- **Validity of machine-coded event data:** checking validity using only published datasets gives little insight into error sources. — [ResearchGate](https://www.researchgate.net/publication/270672494_Using_Machine-Coded_Event_Data_for_the_Micro-Level_Study_of_Political_Violence)
- **LLMs for conflict forecasting:** parametric knowledge is uneven across conflict zones, and retrieval or non-parametric data helps. — [arXiv 2505.09852](https://arxiv.org/pdf/2505.09852)
- **Ukraine-specific forecasting:**
  - A Ukraine–NATO AI forecasts front-line drone attacks from past data, weather and battlefield situation. This is journalism and no paper was found. — [Euromaidan Press](https://euromaidanpress.com/2026/10/14/ukraine-nato-ai-built-to-forecast-russias-front-line-drone-attacks-from-past-data-and-weather-is-ready-to-plug-into-the-army/)
  - Russian equipment losses were forecast with ARIMA, Prophet, LSTM, TCN and XGBoost. — [arXiv 2509.07813](https://arxiv.org/pdf/2509.07813)

### Inferences
Recommended design for an air-raid/strike-intensity project:
1. Use daily counts, for example from the Kaggle Air Force dataset, with a strong autoregressive and seasonal baseline (days since last salvo, weekday, weather, moon phase if relevant).
2. Add exogenous event dummies (diplomatic calls, summits, ultimatums or deadlines, aid and sanctions decisions, Ukrainian deep strikes) with leads and lags. Estimate them through a Poisson or negative binomial count model, or a Hawkes model with marks for event types.
3. Validate with placebo dates and permutation tests, and with rolling out-of-sample evaluation using CRPS.
4. Handle endogeneity: strikes trigger statements (Trump's deadline cuts), and news volume rises *because* of strikes. Use only pre-scheduled diplomatic events (announced summits) as quasi-exogenous shocks, and treat ad-hoc statements carefully.
5. Account for reporting bias: Ukrainian Air Force reporting changed (Aug 2026 break), and Russian MoD claims are biased. GDELT/POLECAT volumes reflect English-media attention more than events.

### Gaps
- POLECAT (the ICEWS successor) and ICEWS-specific forecasting evaluations were not retrieved in this pass.
- The final official ViEWS leaderboard and the JPR publication were not found.
- Full texts of the Mueller & Rauh and Weidmann papers were not read. Their details come from abstracts.
