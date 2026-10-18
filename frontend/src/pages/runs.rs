/*
use leptos::prelude::*;
use leptos_router::hooks::use_params_map;

#[component]
pub fn Runs() -> impl IntoView {
    let params = use_params_map();
    let run_id = move || params.read().get("id").unwrap_or_default();

    view! {
        <section class="evaluation-page">

            <div class="page-header">
                <div>
                    <h1>"Evaluation Results"</h1>
                    <p>{run_id}</p>
                </div>

                <div class="status-badge regression">
                    "Regression"
                </div>
            </div>

            <div class="evaluation-info">
                <strong>"v1.0"</strong>
                <span>" → "</span>
                <strong>"v2.0"</strong>

                <p>"Customer Support Dataset · 50 cases"</p>
            </div>

            <div class="regression-banner">
                <h2>"🔴 Regressions Detected"</h2>
                <p>"6 cases got worse after the prompt changed."</p>
                <p>"2 cases improved."</p>
            </div>

            <div class="metrics-grid">

                <div class="metric-card">
                    <h3>"Category Accuracy"</h3>
                    <div class="metric-value">"92% → 87%"</div>
                    <span>"-5.0%"</span>
                </div>

                <div class="metric-card">
                    <h3>"Summary Quality"</h3>
                    <div class="metric-value">"4.4 → 4.1"</div>
                    <span>"-0.3"</span>
                </div>

                <div class="metric-card">
                    <h3>"Latency"</h3>
                    <div class="metric-value">"1.2s → 1.6s"</div>
                    <span>"+33%"</span>
                </div>

            </div>

            <div class="results-card">

                <div class="results-header">
                    <h2>"Results"</h2>

                    <div class="result-filters">
                        <button>"All 50"</button>
                        <button>"🔴 6 Regressions"</button>
                        <button>"🟢 2 Improvements"</button>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>"Case"</th>
                            <th>"Expected"</th>
                            <th>"Baseline"</th>
                            <th>"Candidate"</th>
                        </tr>
                    </thead>

                    <tbody>

                        <tr>
                            <td>"TC_001"</td>
                            <td>"billing"</td>
                            <td>"billing ✓"</td>
                            <td>"billing ✓"</td>
                        </tr>

                        <tr class="regression-row">
                            <td>"TC_002"</td>
                            <td>"technical"</td>
                            <td>"technical ✓"</td>
                            <td>"general ✗"</td>
                        </tr>

                        <tr>
                            <td>"TC_003"</td>
                            <td>"account"</td>
                            <td>"account ✓"</td>
                            <td>"account ✓"</td>
                        </tr>

                        <tr class="regression-row">
                            <td>"TC_004"</td>
                            <td>"billing"</td>
                            <td>"billing ✓"</td>
                            <td>"general ✗"</td>
                        </tr>

                    </tbody>
                </table>

            </div>

        </section>
    }
}
*/
use leptos::prelude::*;
use leptos_router::hooks::use_params_map;

#[derive(Clone)]
struct CaseResult {
    id: &'static str,
    expected: &'static str,
    baseline: &'static str,
    candidate: &'static str,
    baseline_ok: bool,
    candidate_ok: bool,
}

#[derive(Clone, Copy, PartialEq)]
enum Filter {
    All,
    Regressed,
    Improved,
}

#[component]
pub fn Runs() -> impl IntoView {
    let params = use_params_map();
    let run_id = move || params.read().get("id").unwrap_or_default();

    let cases = vec![
        CaseResult { id: "TC_001", expected: "billing", baseline: "billing", candidate: "billing", baseline_ok: true, candidate_ok: true },
        CaseResult { id: "TC_002", expected: "technical", baseline: "technical", candidate: "general", baseline_ok: true, candidate_ok: false },
        CaseResult { id: "TC_003", expected: "account", baseline: "account", candidate: "account", baseline_ok: true, candidate_ok: true },
        CaseResult { id: "TC_004", expected: "billing", baseline: "billing", candidate: "general", baseline_ok: true, candidate_ok: false },
    ];

    let total = cases.len();
    let regressed_count = cases.iter().filter(|c| c.baseline_ok && !c.candidate_ok).count();
    let improved_count = cases.iter().filter(|c| !c.baseline_ok && c.candidate_ok).count();

    let (filter, set_filter) = signal(Filter::All);

    let filtered_cases = move || {
        cases.iter().cloned().filter(|c| match filter.get() {
            Filter::All => true,
            Filter::Regressed => c.baseline_ok && !c.candidate_ok,
            Filter::Improved => !c.baseline_ok && c.candidate_ok,
        }).collect::<Vec<_>>()
    };

    view! {
        <section class="evaluation-page">
            <div class="page-header">
                <div>
                    <h1>"Evaluation Results"</h1>
                    <p>{run_id}</p>
                </div>
                <div class="status-badge regression">"Regression"</div>
            </div>

            <div class="evaluation-info">
                <strong>"v1.0"</strong>
                <span>" → "</span>
                <strong>"v2.0"</strong>
                <p>"Customer Support Dataset · " {total} " cases"</p>
            </div>

            <div class="regression-banner">
                <h2>"🔴 Regressions Detected"</h2>
                <p>{regressed_count} " cases got worse after the prompt changed."</p>
                <p>{improved_count} " cases improved."</p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>"Category Accuracy"</h3>
                    <div class="metric-value">"92% → 87%"</div>
                    <span>"-5.0%"</span>
                </div>
                <div class="metric-card">
                    <h3>"Summary Quality"</h3>
                    <div class="metric-value">"4.4 → 4.1"</div>
                    <span>"-0.3"</span>
                </div>
                <div class="metric-card">
                    <h3>"Latency"</h3>
                    <div class="metric-value">"1.2s → 1.6s"</div>
                    <span>"+33%"</span>
                </div>
            </div>

            <div class="results-card">
                <div class="results-header">
                    <h2>"Results"</h2>
                    <div class="result-filters">
                        <button
                            class:active=move || filter.get() == Filter::All
                            on:click=move |_| set_filter.set(Filter::All)
                        >
                            "All " {total}
                        </button>
                        <button
                            class:active=move || filter.get() == Filter::Regressed
                            on:click=move |_| set_filter.set(Filter::Regressed)
                        >
                            "🔴 " {regressed_count} " Regressions"
                        </button>
                        <button
                            class:active=move || filter.get() == Filter::Improved
                            on:click=move |_| set_filter.set(Filter::Improved)
                        >
                            "🟢 " {improved_count} " Improvements"
                        </button>
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>"Case"</th>
                            <th>"Expected"</th>
                            <th>"Baseline"</th>
                            <th>"Candidate"</th>
                        </tr>
                    </thead>
                    <tbody>
                        <For each=filtered_cases key=|c| c.id let:case>
                            <tr class:regression-row=move || case.baseline_ok && !case.candidate_ok>
                                <td>{case.id}</td>
                                <td>{case.expected}</td>
                                <td>{case.baseline} " " {if case.baseline_ok { "✓" } else { "✗" }}</td>
                                <td>{case.candidate} " " {if case.candidate_ok { "✓" } else { "✗" }}</td>
                            </tr>
                        </For>
                    </tbody>
                </table>
            </div>
        </section>
    }
}