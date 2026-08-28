use leptos::prelude::*;
use leptos_router::components::*;
use leptos_router::path;

use crate::components::layout::header::Header;
use crate::components::layout::sidebar::Sidebar;

use crate::pages::dashboard::Dashboard;
use crate::pages::datasets::Datasets;
use crate::pages::evaluations::Evaluations;
use crate::pages::prompts::Prompts;
//use crate::pages::regressions::Regressions;
use crate::pages::runs::Runs;
//use crate::pages::settings::Settings;

#[component]
pub fn App() -> impl IntoView {
    view! {
        <Router>

            <div class="app">

                <Header />

                <div class="app-body">

                    <Sidebar />

                    <main class="main-content">

                            <Routes fallback=|| "Page not found.">

                            <Route path=path!("/") view=Dashboard />
                            <Route path=path!("/evaluations") view=Evaluations />
                            <Route path=path!("/evaluations/:id") view=Runs />
                            <Route path=path!("/prompts") view=Prompts />
                            <Route path=path!("/datasets") view=Datasets />
                            //<Route path=path!("/regressions") view=Regressions />
                            //<Route path=path!("/settings") view=Settings />

                        </Routes>

                    </main>

                </div>

            </div>

        </Router>
    }
}