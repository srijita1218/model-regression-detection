use leptos::prelude::*;

#[component]
pub fn MetricCard(
    title: String,
    value: String,
) -> impl IntoView {
    view! {
        <div class="metric-card">
            <p>{title}</p>
            <h2>{value}</h2>
        </div>
    }
}