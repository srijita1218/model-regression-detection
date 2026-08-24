use leptos::prelude::*; //imports leptos functionality (*- everything used my prelude)

mod app;
mod components;
mod pages;

use app::App;

fn main() {
    mount_to_body(App);
}