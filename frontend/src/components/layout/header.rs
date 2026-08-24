use leptos::prelude::*;

#[component]
pub fn Header() -> impl IntoView {
    view! {
        <header class="top-header">

            <div class="brand">
                <h2>"ModelWatch"</h2>
                <p>"LLM Regression Detection System"</p>
            </div>

            <div class="connection-status">
                <span>"Ollama"</span>
                <span>" ● Connected"</span>
            </div>

        </header>
    }
}