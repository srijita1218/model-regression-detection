use leptos::prelude::*;
use leptos_router::hooks::use_navigate;

#[component]
pub fn Evaluations() -> impl IntoView {
    let navigate = use_navigate();

    let run_evaluation = move |_| {
        // TODO: replace with the real run id once you're calling a backend
        let run_id = "RUN-001";
        navigate(&format!("/evaluations/{run_id}"), Default::default());
    };

    view! {
        <section class="evaluation-page">

            <div class="page-header">
                <div>
                    <h1>"New Evaluation"</h1>
                    <p>"Compare two prompt versions against your evaluation dataset."</p>
                </div>
            </div>
            

            <div class="evaluation-card">

                <div class="form-section">
                    <label>"Baseline Prompt"</label>
                    <select>
                        <option>"v1.0 — Initial Prompt"</option>
                        <option>"v1.1 — Improved Classification"</option>
                    </select>
                </div>

                <div class="form-section">
                    <label>"Candidate Prompt"</label>
                    <select>
                        <option>"v2.0 — Improved Classification"</option>
                        <option>"v2.1 — Multilingual Support"</option>
                    </select>
                </div>

                <div class="form-section">
                    <label>"Dataset"</label>
                    <select>
                        <option>"Customer Support v1 — 50 cases"</option>
                        <option>"Customer Support v2 — 100 cases"</option>
                    </select>
                </div>

                <div class="form-section">
                    <label>"Model"</label>
                    <select>
                        <option>"qwen2.5:3b"</option>
                        <option>"llama3.2:3b"</option>
                    </select>
                </div>

                <div class="form-section">
                    <h2>"Evaluation Metrics"</h2>

                    <label class="checkbox-row">
                        <input type="checkbox" checked />
                        <span>"Category Accuracy"</span>
                    </label>

                    <label class="checkbox-row">
                        <input type="checkbox" checked />
                        <span>"Summary Quality"</span>
                    </label>

                    <label class="checkbox-row">
                        <input type="checkbox" checked />
                        <span>"Latency"</span>
                    </label>
                </div>

                <div class="form-actions">
                    <button class="primary-button" on:click=run_evaluation>
                        "Run Evaluation"
                    </button>
                </div>

            </div>
        </section>
    }
}