use leptos::prelude::*;

use crate::components::shared::card::Card;
use crate::components::shared::metric::MetricCard;

#[component]
pub fn Dashboard() -> impl IntoView {
    view! {
        <section class="page">

            <div class="page-header">
                <div>
                    <h1>"Dashboard"</h1>
                    <p>
                        "Monitor your LLM quality and detect regressions."
                    </p>
                </div>
            </div>

            <h2 class="section-title">
                "Model Evaluation"
            </h2>

            <Card title="Latest Evaluation".to_string()>
                <div class="latest-evaluation">

                    <div class="evaluation-version">
                        <span>"v1.0"</span>
                        <span class="version-arrow">"→"</span>
                        <span>"v2.0"</span>
                    </div>

                    <div class="evaluation-status">
                        <span class="status-dot"></span>
                        <span class="status-danger">
                            "Regression Detected"
                        </span>

                    </div>

                    <div class="evaluation-stats">

                        <div class="evaluation-stat">
                            <span>"Accuracy"</span>
                            <strong>"92% → 87%"</strong>
                        </div>

                        <div class="evaluation-stat">
                            <span>"Regressions"</span>
                            <strong>"6"</strong>
                        </div>

                        <div class="evaluation-stat">
                            <span>"Improvements"</span>
                            <strong>"2"</strong>
                        </div>

                    </div>

                    <button class="text-button">
                        "View Results"
                    </button>

                </div>
            </Card>

            <div class="metric-grid dashboard-metrics">

                <MetricCard
                    title="Accuracy".to_string()
                    value="87.2%".to_string()
                />

                <MetricCard
                    title="Evaluations".to_string()
                    value="12".to_string()
                />

            </div>

            <div class="dashboard-actions">
                <button class="primary-button">
                    "+ New Evaluation"
                </button>
            </div>

        </section>
    }
}