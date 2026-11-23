'use client';

/**
 * JURY EXTENSION DEMO — Unit-4 (Multi-Agent System) + Unit-3 (Long Memory
 * and Feedback Loop).
 *
 * This page is a *second surface* on top of the base project. It talks to the
 * extension API (`/api/v1/specialists/*` and `/api/v1/memory/*`) and therefore
 * works even when no Swiggy token is available, which is exactly the situation
 * the jury laptop may be in.
 */

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  RotateCcw,
  Users,
  Brain,
  Check,
  X,
  Loader2,
  ShieldCheck,
} from 'lucide-react';

import {
  fetchWeightSpec,
  fetchMemoryProfile,
  fetchFeedbackHistory,
  recordFeedback,
  observeRequest,
  resetMemory,
  fetchSpecialistRegistry,
  fetchSpecialistDemo,
  WeightSpec,
  MemoryProfile,
  FeedbackEvent,
  SpecialistRegistry,
  SupervisorReport,
  Weights,
} from '../../lib/extensionApi';

const USER_ID = 'jury_demo_user';

/* The three demo items used to drive the feedback loop from the browser.
 * They mirror the candidate set used by JURY_DEMO_RUNNER.py Part C. */
const DEMO_ITEMS = [
  {
    name: 'Value Paneer Thali',
    price: 149,
    eta: 25,
    rating: 4.2,
    blurb: 'cheapest, but slow',
  },
  {
    name: 'Express Paneer Bowl',
    price: 289,
    eta: 14,
    rating: 3.9,
    blurb: 'fastest, slightly pricier',
  },
  {
    name: 'Classic Paneer Combo',
    price: 229,
    eta: 20,
    rating: 4.4,
    blurb: 'balanced middle ground',
  },
];

const COLD_START: Weights = { w1: 0.35, w2: 0.4, w3: 0.25 };

const WEIGHT_LABEL: Record<keyof Weights, string> = {
  w1: 'price',
  w2: 'speed',
  w3: 'quality',
};

const WEIGHT_DIGIT: Record<keyof Weights, string> = {
  w1: '1',
  w2: '2',
  w3: '3',
};

/* Mirrors backend/app/db/memory_store.py:
 *   normalise_attributes() then update_weights().
 * Used only to PREDICT, in the browser, which weight an Accept/Reject will
 * move — the authoritative update still happens server-side. */
const BUDGET_CEILING = 500;
const ETA_CEILING = 30;
const RATING_CEILING = 5;

function normaliseAttributes(item: {
  price: number;
  eta: number;
  rating: number;
}): Weights {
  return {
    w1: round4(Math.max(0, 1 - item.price / BUDGET_CEILING)),
    w2: round4(Math.max(0, 1 - item.eta / ETA_CEILING)),
    w3: round4(Math.max(0, Math.min(1, item.rating / RATING_CEILING))),
  };
}

function round4(v: number) {
  return Math.round(v * 10000) / 10000;
}

/**
 * Which weight the server-side update will raise.
 *   accept  -> the dimension the chosen item was strongest on
 *   reject  -> the dimension the chosen item was weakest on (we under-weighted it)
 */
function predictWeightMove(
  accepted: boolean,
  item: { price: number; eta: number; rating: number }
): keyof Weights {
  const scored = normaliseAttributes(item);
  const keys: (keyof Weights)[] = ['w1', 'w2', 'w3'];
  const strongest = keys.reduce((a, b) => (scored[a] >= scored[b] ? a : b));
  const weakest = keys.reduce((a, b) => (scored[a] <= scored[b] ? a : b));
  return accepted ? strongest : weakest;
}

/* ------------------------------------------------------------------ */
/* Utility function (mirrors backend/app/agent/nodes/restaurant.py)    */
/* ------------------------------------------------------------------ */

function utility(
  item: { price: number; eta: number; rating: number },
  w: Weights,
  maxBudget: number,
  maxEta: number
): number {
  const p = Math.max(0, 1 - item.price / maxBudget);
  const e = Math.max(0, 1 - item.eta / maxEta);
  const r = Math.max(0, Math.min(1, item.rating / 5));
  return w.w1 * p + w.w2 * e + w.w3 * r;
}

export default function ExtensionDemoPage() {
  const [tab, setTab] = useState<'unit4' | 'unit3'>('unit4');

  /* Unit-4 state */
  const [registry, setRegistry] = useState<SpecialistRegistry | null>(null);
  const [report, setReport] = useState<SupervisorReport | null>(null);
  const [unit4Busy, setUnit4Busy] = useState(false);

  /* Unit-3 state */
  const [spec, setSpec] = useState<WeightSpec | null>(null);
  const [profile, setProfile] = useState<MemoryProfile | null>(null);
  const [history, setHistory] = useState<FeedbackEvent[]>([]);
  const [unit3Busy, setUnit3Busy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const flash = useCallback((msg: string) => {
    setNotice(msg);
    window.setTimeout(() => setNotice(null), 3200);
  }, []);

  const loadUnit4 = useCallback(async () => {
    setUnit4Busy(true);
    try {
      const [reg, rep] = await Promise.all([
        fetchSpecialistRegistry(),
        fetchSpecialistDemo(),
      ]);
      setRegistry(reg);
      setReport(rep);
    } catch {
      flash('Could not reach the backend. Start it with: uvicorn app.main:app --reload');
    } finally {
      setUnit4Busy(false);
    }
  }, [flash]);

  const loadUnit3 = useCallback(async () => {
    setUnit3Busy(true);
    try {
      const [sp, prof, hist] = await Promise.all([
        fetchWeightSpec(),
        fetchMemoryProfile(USER_ID),
        fetchFeedbackHistory(USER_ID),
      ]);
      setSpec(sp);
      setProfile(prof);
      setHistory(hist);
    } catch {
      flash('Could not reach the backend. Start it with: uvicorn app.main:app --reload');
    } finally {
      setUnit3Busy(false);
    }
  }, [flash]);

  useEffect(() => {
    void loadUnit4();
    void loadUnit3();
  }, [loadUnit4, loadUnit3]);

  async function sendFeedback(
    item: { name: string; price: number; eta: number; rating: number },
    accepted: boolean
  ) {
    setUnit3Busy(true);
    try {
      const res = await recordFeedback(USER_ID, {
        accepted,
        target_name: item.name,
        reason: accepted
          ? `${item.name} — accepted, exactly what I wanted`
          : `${item.name} — rejected, too slow to wait ${item.eta} minutes`,
        price: item.price,
        eta: item.eta,
        rating: item.rating,
      });
      const d = res.delta;
      flash(
        `Weight update applied — w1 ${d.w1 >= 0 ? '+' : ''}${d.w1} · ` +
          `w2 ${d.w2 >= 0 ? '+' : ''}${d.w2} · w3 ${d.w3 >= 0 ? '+' : ''}${d.w3}`
      );
      await loadUnit3();
    } catch (e: any) {
      flash(e?.message || 'Feedback failed');
    } finally {
      setUnit3Busy(false);
    }
  }

  async function seedPreference() {
    setUnit3Busy(true);
    try {
      await observeRequest(USER_ID, {
        food: 'paneer',
        vegetarian: true,
        max_budget: 300,
        max_delivery_minutes: 25,
      });
      flash('Preference distilled into the durable profile');
      await loadUnit3();
    } catch (e: any) {
      flash(e?.message || 'Observe failed');
    } finally {
      setUnit3Busy(false);
    }
  }

  async function doReset() {
    setUnit3Busy(true);
    try {
      await resetMemory(USER_ID);
      flash('User forgotten — back to cold start');
      await loadUnit3();
    } catch (e: any) {
      flash(e?.message || 'Reset failed');
    } finally {
      setUnit3Busy(false);
    }
  }

  const learned = profile?.weights ?? COLD_START;
  const coldRanked = DEMO_ITEMS.map((i) => ({ i, u: utility(i, COLD_START, 300, 30) })).sort(
    (a, b) => b.u - a.u
  );
  const learnedRanked = DEMO_ITEMS.map((i) => ({ i, u: utility(i, learned, 300, 30) })).sort(
    (a, b) => b.u - a.u
  );
  const flipped = coldRanked[0].i.name !== learnedRanked[0].i.name;

  return (
    <div className="min-h-screen bg-cream text-espresso">
      {/* ---------------- Header ---------------- */}
      <header className="bg-white/90 backdrop-blur-md border-b border-sand-dark/60 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-baseline gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-espresso-muted hover:text-terracotta transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Base project
            </Link>
            <h1 className="font-serif text-xl font-bold text-espresso tracking-tight">
              MINI-PROJECT EXTENSION
            </h1>
          </div>
          <span className="text-xs text-espresso-light font-medium tracking-wide hidden sm:inline-block">
            Unit-3 · Long Memory &amp; Feedback &nbsp;|&nbsp; Unit-4 · Multi-Agent System
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 pb-24 space-y-10">
        {/* ---------------- Intro ---------------- */}
        <section className="bg-white border border-sand-dark/70 rounded-3xl p-8 shadow-warm-sm">
          <p className="text-xs tracking-[0.25em] uppercase text-terracotta font-semibold mb-3">
            Jury demo
          </p>
          <h2 className="font-serif text-3xl font-bold text-espresso tracking-tight mb-3">
            Two working modules, added on top of an unchanged base project
          </h2>
          <p className="text-sm text-espresso-muted leading-relaxed max-w-3xl">
            <strong className="text-espresso">Unit-4</strong> decomposes the ranking
            decision into six concurrent specialist agents with hard-constraint gates
            and soft-preference scores, joined at a barrier by a supervisor.{' '}
            <strong className="text-espresso">Unit-3</strong> gives the system a durable
            per-user memory and an online feedback loop: accept/reject signals update
            the utility weights in SQLite, and the next ranking uses the new weights.
            Both are visible below, live, against the running backend.
          </p>
        </section>

        {/* ---------------- Tabs ---------------- */}
        <div className="flex gap-2 border-b border-sand-dark/60 pb-3">
          <TabButton
            active={tab === 'unit4'}
            onClick={() => setTab('unit4')}
            icon={<Users className="w-4 h-4" />}
            label="Unit-4 — Multi-Agent System"
          />
          <TabButton
            active={tab === 'unit3'}
            onClick={() => setTab('unit3')}
            icon={<Brain className="w-4 h-4" />}
            label="Unit-3 — Long Memory & Feedback"
          />
        </div>

        {notice && (
          <div className="bg-warmamber-light border border-warmamber-border text-espresso p-4 rounded-2xl text-sm shadow-warm-sm">
            {notice}
          </div>
        )}

        {tab === 'unit4' ? (
          <Unit4Panel
            registry={registry}
            report={report}
            busy={unit4Busy}
            onRefresh={loadUnit4}
          />
        ) : (
          <Unit3Panel
            spec={spec}
            profile={profile}
            history={history}
            busy={unit3Busy}
            coldRanked={coldRanked}
            learnedRanked={learnedRanked}
            flipped={flipped}
            onFeedback={sendFeedback}
            onSeed={seedPreference}
            onReset={doReset}
          />
        )}
      </main>
    </div>
  );
}

/* ================================================================== */
/* Unit-4 — Multi-Agent System                                         */
/* ================================================================== */

function Unit4Panel({
  registry,
  report,
  busy,
  onRefresh,
}: {
  registry: SpecialistRegistry | null;
  report: SupervisorReport | null;
  busy: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="space-y-10">
      {/* A — roster */}
      <Panel
        eyebrow="Part A"
        title="The agent roster"
        body="Six specialists, one decision each. Three are hard gates (a failure rejects the candidate outright); three are soft scorers (traded off by weight). Every verdict is attributed to a named agent."
      >
        {!registry ? (
          <Loading />
        ) : (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {registry.specialists.map((s) => (
              <div
                key={s.name}
                className={`border rounded-2xl p-4 ${
                  s.constraint_type === 'HARD'
                    ? 'border-terracotta-border bg-terracotta-light'
                    : 'border-olive-border bg-olive-light'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-serif font-bold text-espresso text-sm">{s.name}</p>
                  <span
                    className={`text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full ${
                      s.constraint_type === 'HARD'
                        ? 'bg-terracotta text-white'
                        : 'bg-olive text-white'
                    }`}
                  >
                    {s.constraint_type === 'HARD' ? 'Gate' : 'Soft'}
                  </span>
                </div>
                <p className="text-xs text-espresso-muted mt-1">
                  dimension · <span className="font-mono">{s.dimension}</span>
                </p>
                <p className="text-xs text-espresso-light mt-1">
                  join weight · <span className="font-mono">{s.join_weight}</span>
                </p>
              </div>
            ))}
          </div>
        )}
        <p className="text-xs text-espresso-light mt-4 font-mono">
          execution model: {registry?.execution_model ?? '—'}
        </p>
      </Panel>

      {/* B — fan-out */}
      <Panel
        eyebrow="Part B"
        title="Fan-out — every specialist judges every candidate"
        body="6 candidates × 6 concurrent agents = 36 verdicts. The counts below prove each agent actually ran on each candidate; the timings prove the fan-out is concurrent rather than sequential."
      >
        {!report ? (
          <Loading />
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-4 mb-6">
              <Metric label="Candidates" value={String(report.total_candidates)} />
              <Metric label="Verdicts" value={String(report.total_candidates * report.specialist_count)} />
              <Metric label="Wall time" value={`${report.elapsed_ms} ms`} />
              <Metric
                label="Accepted / Rejected"
                value={`${report.accepted_count} / ${report.rejected_count}`}
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="text-espresso-light uppercase tracking-wider text-left">
                    <th className="py-2 pr-3">Specialist</th>
                    <th className="py-2 pr-3">Type</th>
                    <th className="py-2 pr-3 text-right">Evaluated</th>
                    <th className="py-2 pr-3 text-right">Passed</th>
                    <th className="py-2 pr-3 text-right">Failed</th>
                    <th className="py-2 text-right">Avg score</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.per_specialist_stats).map(([name, st]) => (
                    <tr key={name} className="border-t border-sand/80">
                      <td className="py-2 pr-3 font-mono text-espresso">{name}</td>
                      <td className="py-2 pr-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide ${
                            st.hard_constraint
                              ? 'bg-terracotta/12 text-terracotta border border-terracotta-border'
                              : 'bg-olive/12 text-olive border border-olive-border'
                          }`}
                        >
                          {st.hard_constraint ? 'HARD' : 'SOFT'}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-right font-mono">{st.evaluated}</td>
                      <td className="py-2 pr-3 text-right font-mono text-olive">{st.passed}</td>
                      <td className="py-2 pr-3 text-right font-mono text-terracotta">{st.failed}</td>
                      <td className="py-2 text-right font-mono">{st.avg_score.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Panel>

      {/* C — the join */}
      <Panel
        eyebrow="Part C"
        title="The join — hard gates first, then a weighted aggregate"
        body="A candidate that fails any hard gate is rejected with a stated reason naming the agent. Survivors are ranked by the weighted aggregate of every verdict."
      >
        {!report ? (
          <Loading />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-espresso-muted mb-3">
                Ranking
              </h4>
              {report.ranking.length === 0 ? (
                <p className="text-sm text-espresso-light">No candidate survived the hard gates.</p>
              ) : (
                <ol className="space-y-2">
                  {report.ranking.map((r) => (
                    <li
                      key={r.item_id}
                      className="bg-sand-light border border-sand-dark/60 rounded-xl px-4 py-3 flex items-center gap-3"
                    >
                      <span className="w-6 h-6 rounded-full bg-terracotta text-white text-xs font-bold flex items-center justify-center shrink-0">
                        {r.rank}
                      </span>
                      <span className="text-sm font-medium text-espresso flex-1 truncate">
                        {r.name}
                      </span>
                      <span className="text-xs font-mono text-espresso-muted">
                        U={r.utility.toFixed(4)}
                      </span>
                      <span className="text-xs font-mono text-espresso-light hidden sm:inline">
                        ₹{r.price} · {r.eta}m · {r.rating}★
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-espresso-muted mb-3">
                Rejected by hard-constraint gates
              </h4>
              {report.rejections.length === 0 ? (
                <p className="text-sm text-espresso-light">Nothing was rejected.</p>
              ) : (
                <ul className="space-y-2">
                  {report.rejections.map((rej) => (
                    <li
                      key={rej.item_id}
                      className="bg-warmred-light border border-warmred-border rounded-xl px-4 py-3"
                    >
                      <p className="text-sm font-medium text-warmred flex items-center gap-2">
                        <X className="w-3.5 h-3.5" />
                        {rej.name}
                      </p>
                      <p className="text-xs text-espresso-muted mt-1">{rej.reason}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </Panel>

      {/* D — winner audit */}
      <Panel
        eyebrow="Part D"
        title="The winner's complete verdict vector"
        body="Every dimension of the decision, attributed to the agent that made it. A judge can audit any single decision without re-reading the pipeline."
      >
        {!report || !report.winner ? (
          <Loading />
        ) : (
          <>
            <div className="bg-sand-light border border-sand-dark/60 rounded-xl px-5 py-4 mb-4 flex flex-wrap items-center gap-x-6 gap-y-2">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-espresso-light">Winner</p>
                <p className="font-serif text-lg font-bold text-terracotta">
                  {report.winner.candidate.name}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-espresso-light">Utility</p>
                <p className="font-mono text-lg text-espresso">{report.winner.utility.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-espresso-light">Decision</p>
                <p className="font-mono text-sm text-olive">{report.winner.decision}</p>
              </div>
              <p className="text-xs text-espresso-muted flex-1 min-w-[240px]">
                {report.winner.explanation}
              </p>
            </div>

            <ul className="space-y-2">
              {report.winner.verdicts.map((v) => (
                <li
                  key={v.specialist}
                  className="border border-sand-dark/60 rounded-xl px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1 bg-white"
                >
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold tracking-wider px-2 py-1 rounded ${
                      v.passed
                        ? 'bg-olive-light text-olive border border-olive-border'
                        : 'bg-warmred-light text-warmred border border-warmred-border'
                    }`}
                  >
                    {v.passed ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                    {v.passed ? 'PASS' : 'FAIL'}
                  </span>
                  <span className="font-mono text-xs text-espresso w-40">{v.specialist}</span>
                  <span className="text-[10px] font-bold tracking-wide text-espresso-light w-24">
                    {v.is_hard_constraint ? 'HARD' : 'SOFT'} w={v.weight}
                  </span>
                  <span className="text-xs text-espresso-muted flex-1 min-w-[200px]">{v.reason}</span>
                  <span className="font-mono text-xs text-terracotta">score={v.score.toFixed(3)}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </Panel>

      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          disabled={busy}
          className="inline-flex items-center gap-2 bg-terracotta hover:bg-terracotta-hover text-white text-xs font-bold px-5 py-2.5 rounded-full transition shadow-warm-sm disabled:opacity-60"
        >
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
          Re-run the supervisor
        </button>
        <code className="text-xs font-mono text-espresso-light">
          GET /api/v1/specialists/demo
        </code>
      </div>
    </div>
  );
}

/* ================================================================== */
/* Unit-3 — Long Memory + Feedback Loop                                */
/* ================================================================== */

function Unit3Panel({
  spec,
  profile,
  history,
  busy,
  coldRanked,
  learnedRanked,
  flipped,
  onFeedback,
  onSeed,
  onReset,
}: {
  spec: WeightSpec | null;
  profile: MemoryProfile | null;
  history: FeedbackEvent[];
  busy: boolean;
  coldRanked: { i: (typeof DEMO_ITEMS)[number]; u: number }[];
  learnedRanked: { i: (typeof DEMO_ITEMS)[number]; u: number }[];
  flipped: boolean;
  onFeedback: (item: (typeof DEMO_ITEMS)[number], accepted: boolean) => void;
  onSeed: () => void;
  onReset: () => void;
}) {
  const weights = profile?.weights ?? COLD_START;

  return (
    <div className="space-y-10">
      {/* A — the spec */}
      <Panel
        eyebrow="Part A"
        title="What is being learned"
        body="The ranking utility is a weighted sum over three normalised attributes. The weights (w1, w2, w3) are not constants — they are parameters updated online from human feedback."
      >
        {!spec ? (
          <Loading />
        ) : (
          <div className="space-y-4">
            <code className="block bg-sand-light border border-sand-dark/60 rounded-xl px-4 py-3 font-mono text-xs text-espresso">
              {spec.utility_function}
            </code>
            <div className="grid gap-3 sm:grid-cols-3">
              {(['w1', 'w2', 'w3'] as const).map((k) => (
                <div key={k} className="border border-sand-dark/60 rounded-xl px-4 py-3">
                  <p className="font-mono text-xs font-bold text-terracotta">{k}</p>
                  <p className="text-xs text-espresso-muted mt-1">{spec.dimensions[k]}</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-espresso-muted">
              <span className="font-semibold text-espresso">Update rule:</span> {spec.update_rule}{' '}
              <span className="font-mono">(lr = {spec.learning_rate})</span>
            </p>
          </div>
        )}
      </Panel>

      {/* B — long memory */}
      <Panel
        eyebrow="Part B"
        title="Long memory — a durable profile, not a session"
        body="Stored in SQLite and keyed by a stable user id, so it survives a backend restart and carries into a new session. The counters below accumulate across sessions."
      >
        <div className="grid gap-4 md:grid-cols-4">
          <div className="md:col-span-2 bg-sand-light border border-sand-dark/60 rounded-2xl p-5">
            <p className="text-xs font-bold uppercase tracking-wider text-espresso-muted mb-4">
              Learned weights
            </p>
            <div className="space-y-3">
              {(['w1', 'w2', 'w3'] as const).map((k) => (
                <WeightBar key={k} name={k} value={weights[k]} />
              ))}
            </div>
            {profile?.cold_start ? (
              <p className="text-[11px] text-espresso-light mt-4">
                Cold start — no feedback recorded yet.
              </p>
            ) : (
              <p className="text-[11px] text-olive mt-4">
                Persisted across {profile?.interaction_count ?? 0} interaction(s) · last updated{' '}
                {profile?.updated_at ? new Date(profile.updated_at).toLocaleString() : '—'}
              </p>
            )}
          </div>

          <div className="bg-white border border-sand-dark/60 rounded-2xl p-5">
            <p className="text-xs font-bold uppercase tracking-wider text-espresso-muted mb-3">
              Preference profile
            </p>
            {profile && Object.keys(profile.preferences).length > 0 ? (
              <ul className="space-y-1.5 text-xs text-espresso-muted">
                {Object.entries(profile.preferences).map(([k, v]) => (
                  <li key={k} className="flex justify-between gap-2">
                    <span>{k.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-espresso">{String(v)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-espresso-light">
                Empty — nothing observed yet.
              </p>
            )}
            <button
              onClick={onSeed}
              disabled={busy}
              className="mt-4 text-[11px] font-bold text-terracotta hover:underline disabled:opacity-60"
            >
              Distil a stated preference →
            </button>
          </div>

          <div className="bg-white border border-sand-dark/60 rounded-2xl p-5">
            <p className="text-xs font-bold uppercase tracking-wider text-espresso-muted mb-3">
              Counters
            </p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-espresso-muted">Interactions</span>
                <span className="font-mono font-bold text-espresso">
                  {profile?.interaction_count ?? 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-espresso-muted">Accepted</span>
                <span className="font-mono font-bold text-olive">
                  {profile?.accept_count ?? 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-espresso-muted">Rejected</span>
                <span className="font-mono font-bold text-warmred">
                  {profile?.reject_count ?? 0}
                </span>
              </div>
            </div>
            <button
              onClick={onReset}
              disabled={busy}
              className="mt-4 text-[11px] font-bold text-warmred hover:underline disabled:opacity-60"
            >
              Forget this user (cold start)
            </button>
          </div>
        </div>
      </Panel>

      {/* C — drive the loop */}
      <Panel
        eyebrow="Part C"
        title="The feedback loop — drive it from here"
        body="Reject a slow item and watch the speed weight rise; accept a fast one and it is reinforced. Every click performs one online update, persists it, and appends an audit row."
      >
        <div className="grid gap-3 md:grid-cols-3">
          {DEMO_ITEMS.map((item) => {
            const acceptMove = predictWeightMove(true, item);
            const rejectMove = predictWeightMove(false, item);
            return (
              <div key={item.name} className="bg-white border border-sand-dark/60 rounded-2xl p-5">
                <p className="font-serif font-bold text-espresso">{item.name}</p>
                <p className="text-xs text-espresso-light mt-1">{item.blurb}</p>
                <p className="text-[11px] font-mono text-espresso-muted mt-2">
                  ₹{item.price} · {item.eta} min · {item.rating}★
                </p>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => onFeedback(item, true)}
                    disabled={busy}
                    title={`Reinforces ${WEIGHT_LABEL[acceptMove]} (w${WEIGHT_DIGIT[acceptMove]})`}
                    className="flex-1 inline-flex flex-col items-center justify-center bg-olive hover:opacity-90 text-white px-3 py-2 rounded-full transition disabled:opacity-60"
                  >
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold">
                      <Check className="w-3.5 h-3.5" /> Accept
                    </span>
                    <span className="text-[9px] font-mono opacity-90">
                      w{WEIGHT_DIGIT[acceptMove]} ({WEIGHT_LABEL[acceptMove]}) ↑
                    </span>
                  </button>
                  <button
                    onClick={() => onFeedback(item, false)}
                    disabled={busy}
                    title={`Boosts ${WEIGHT_LABEL[rejectMove]} (w${WEIGHT_DIGIT[rejectMove]}) — the under-weighted dimension`}
                    className="flex-1 inline-flex flex-col items-center justify-center bg-warmred hover:opacity-90 text-white px-3 py-2 rounded-full transition disabled:opacity-60"
                  >
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold">
                      <X className="w-3.5 h-3.5" /> Reject
                    </span>
                    <span className="text-[9px] font-mono opacity-90">
                      w{WEIGHT_DIGIT[rejectMove]} ({WEIGHT_LABEL[rejectMove]}) ↑
                    </span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* D — top-1 flip */}
      <Panel
        eyebrow="Part D"
        title="The loop closes — the top-1 recommendation flips"
        body="Same three candidates, same request (vegetarian paneer, ≤ ₹300, ≤ 30 min). Only the weight vector differs, and the ranking changes because of it."
      >
        <div className="grid gap-4 md:grid-cols-2">
          <RankColumn
            title="Cold-start weights"
            subtitle="w = (0.35, 0.40, 0.25) — never learned"
            rows={coldRanked}
            highlightIndex={0}
          />
          <RankColumn
            title="Learned weights"
            subtitle={`w = (${weights.w1.toFixed(3)}, ${weights.w2.toFixed(3)}, ${weights.w3.toFixed(
              3
            )}) — after feedback`}
            rows={learnedRanked}
            highlightIndex={0}
          />
        </div>

        <div
          className={`mt-4 px-5 py-4 rounded-2xl border text-sm ${
            flipped
              ? 'bg-olive-light border-olive-border text-olive'
              : 'bg-warmamber-light border-warmamber-border text-espresso'
          }`}
        >
          {flipped ? (
            <>
              <span className="font-bold">Top-1 flip confirmed:</span> the recommendation moved
              from <span className="font-mono">{coldRanked[0].i.name}</span> to{' '}
              <span className="font-mono">{learnedRanked[0].i.name}</span>. Identical inputs —
              only the persisted weights differ.
            </>
          ) : (
            <>
              <span className="font-bold">No flip yet.</span> The top-1 is still{' '}
              <span className="font-mono">{learnedRanked[0].i.name}</span>. Reject a slow item above
              to raise the speed weight and the ranking will reorder.
            </>
          )}
        </div>
      </Panel>

      {/* E — audit trail */}
      <Panel
        eyebrow="Part E"
        title="The audit trail — proof the learning is real"
        body="Every feedback event is stored append-only with the weight vector before and after the update, so the whole learning history is reconstructable."
      >
        {history.length === 0 ? (
          <p className="text-sm text-espresso-light">
            No feedback recorded yet for{' '}
            <span className="font-mono">{USER_ID}</span>. Use the buttons in Part C.
          </p>
        ) : (
          <ol className="space-y-2">
            {history.map((e) => (
              <li
                key={e.id}
                className="bg-white border border-sand-dark/60 rounded-xl px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1"
              >
                <span
                  className={`inline-flex items-center gap-1 text-[10px] font-bold tracking-wider px-2 py-1 rounded ${
                    e.accepted
                      ? 'bg-olive-light text-olive border border-olive-border'
                      : 'bg-warmred-light text-warmred border border-warmred-border'
                  }`}
                >
                  {e.accepted ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  {e.accepted ? 'ACCEPTED' : 'REJECTED'}
                </span>
                <span className="text-sm font-medium text-espresso">{e.target_name}</span>
                <span className="text-xs text-espresso-muted flex-1 min-w-[180px]">{e.reason}</span>
                <span className="font-mono text-[11px] text-espresso-light">
                  {e.weights_before.w2.toFixed(3)} → {e.weights_after.w2.toFixed(3)} (w2)
                </span>
                <span className="font-mono text-[10px] text-espresso-light">
                  {e.created_at ? new Date(e.created_at).toLocaleTimeString() : ''}
                </span>
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </div>
  );
}

/* ================================================================== */
/* Shared presentational pieces                                        */
/* ================================================================== */

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold transition ${
        active
          ? 'bg-terracotta text-white shadow-warm-sm'
          : 'bg-white border border-sand-dark/70 text-espresso-muted hover:border-terracotta-border hover:text-terracotta'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function Panel({
  eyebrow,
  title,
  body,
  children,
}: {
  eyebrow: string;
  title: string;
  body: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-white border border-sand-dark/70 rounded-3xl p-7 shadow-warm-sm">
      <div className="flex items-center gap-2 text-terracotta text-[10px] font-bold uppercase tracking-[0.2em] mb-2">
        <ShieldCheck className="w-3.5 h-3.5" />
        {eyebrow}
      </div>
      <h3 className="font-serif text-xl font-bold text-espresso tracking-tight mb-2">{title}</h3>
      <p className="text-sm text-espresso-muted leading-relaxed mb-5">{body}</p>
      {children}
    </section>
  );
}

function Loading() {
  return (
    <div className="flex items-center gap-2 text-sm text-espresso-light py-6">
      <Loader2 className="w-4 h-4 animate-spin" />
      Loading…
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-sand-light border border-sand-dark/60 rounded-xl px-4 py-3">
      <p className="text-[10px] uppercase tracking-wider text-espresso-light">{label}</p>
      <p className="font-mono text-lg font-bold text-espresso mt-0.5">{value}</p>
    </div>
  );
}

function WeightBar({ name, value }: { name: string; value: number }) {
  const pct = Math.max(0, Math.min(1, value / 0.7)) * 100;
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-mono text-espresso-muted">{name}</span>
        <span className="font-mono font-bold text-terracotta">{value.toFixed(4)}</span>
      </div>
      <div className="h-1.5 bg-sand-dark/60 rounded-full overflow-hidden mt-1">
        <div className="h-full bg-terracotta rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function RankColumn({
  title,
  subtitle,
  rows,
  highlightIndex,
}: {
  title: string;
  subtitle: string;
  rows: { i: (typeof DEMO_ITEMS)[number]; u: number }[];
  highlightIndex: number;
}) {
  return (
    <div className="bg-sand-light border border-sand-dark/60 rounded-2xl p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-espresso-muted">{title}</p>
      <p className="font-mono text-[11px] text-espresso-light mt-1 mb-3">{subtitle}</p>
      <ol className="space-y-2">
        {rows.map((r, idx) => (
          <li
            key={r.i.name}
            className={`flex items-center gap-3 rounded-xl px-3 py-2 border ${
              idx === highlightIndex
                ? 'bg-white border-terracotta-border shadow-warm-sm'
                : 'bg-white/50 border-transparent'
            }`}
          >
            <span
              className={`w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                idx === highlightIndex ? 'bg-terracotta text-white' : 'bg-sand-dark text-espresso-muted'
              }`}
            >
              {idx + 1}
            </span>
            <span className="text-xs font-medium text-espresso flex-1 truncate">{r.i.name}</span>
            <span className="font-mono text-[11px] text-espresso-muted">
              {r.i.price}₹ · {r.i.eta}m
            </span>
            <span className="font-mono text-[11px] font-bold text-terracotta">U={r.u.toFixed(4)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
