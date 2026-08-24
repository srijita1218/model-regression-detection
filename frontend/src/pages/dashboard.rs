use leptos::prelude::*;

#[component]
pub fn Dashboard() -> impl IntoView {
    view! {
        <section>
            <h1>"Dashboard"</h1>

            <p>
                "Monitor your LLM quality and detect regressions."
            </p>
        </section>
    }
}