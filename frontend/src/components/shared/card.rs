#![allow(dead_code)]

use leptos::prelude::*;

#[component]
pub fn Card(
    title: String,
    children: Children, //card can contain other UI elements inside itself
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