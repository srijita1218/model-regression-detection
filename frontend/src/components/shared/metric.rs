#![allow(dead_code)]

use leptos::prelude::*;

#[allow(dead_code)]
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