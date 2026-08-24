use leptos::prelude::*;

#[component]
pub fn Card(
    title: String,
    children: Children,
) -> impl IntoView {
    view! {
        <div class="card">
            <h3>{title}</h3>

            <div class="card-content">
                {children()}
            </div>
        </div>
    }
}