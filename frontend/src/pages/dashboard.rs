use leptos::prelude::*;
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

            <div class="metric-grid">
                <MetricCard
                    title="Total Runs".to_string()
                    value="128".to_string()
                />

                <MetricCard
                    title="Evaluations".to_string()
                    value="96".to_string()
                />

                <MetricCard
                    title="Success Rate".to_string()
                    value="94.2%".to_string()
                />

                <MetricCard
                    title="Regressions".to_string()
                    value="7".to_string()
                />
            </div>
        </section>
    }
}