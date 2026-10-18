use leptos::prelude::*;
use leptos_router::components::A;

#[component]
pub fn Sidebar() -> impl IntoView {
    view! {
        <aside class="sidebar">

            <div class="sidebar-title">
                "Navigation"
            </div>

            <nav class="sidebar-nav">

                <A href="/">"Dashboard"</A>
                <A href="/evaluations">"Evaluations"</A>
                <A href="/prompts">"Prompts"</A>
                <A href="/datasets">"Datasets"</A>
                //<A href="/runs">"Runs"</A>
                //<A href="/regressions">"Regressions"</A>
                //<A href="/settings">"Settings"</A>

            </nav>

        </aside>
    }
}