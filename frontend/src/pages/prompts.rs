use leptos::either::Either;
use leptos::prelude::*;

#[derive(Clone)]
struct PromptVersion {
    version: String,
    description: String,
    status: String,
    date: String,
    content: String,
}

#[component]
pub fn Prompts() -> impl IntoView {
    let versions = vec![
        PromptVersion {
            version: "v2.0".to_string(),
            description: "Improved multilingual classification".to_string(),
            status: "CURRENT".to_string(),
            date: "Aug 30, 2026".to_string(),
            content: "You are a multilingual customer support classification assistant. Analyze the customer's message and classify it into the appropriate support category.".to_string(),
        },
        PromptVersion {
            version: "v1.0".to_string(),
            description: "Initial customer support design".to_string(),
            status: "BASELINE".to_string(),
            date: "Aug 28, 2026".to_string(),
            content: "You are a customer support assistant. Classify the customer's message into the appropriate support category.".to_string(),
        },
    ];

    let selected_version = RwSignal::new(None::<PromptVersion>);

    let comparison = RwSignal::new(
        None::<(PromptVersion, PromptVersion)>
    );

    let versions_for_reactive = versions.clone();

    view! {
        <section class="page prompts-page">

            {move || {

                let versions_for_view = versions_for_reactive.clone();
                let versions_for_detail = versions_for_reactive.clone();
                let versions_for_list = versions_for_reactive.clone();

                if let Some((old_version, new_version)) = comparison.get() {
                    return Either::Left(view! {

                        <div>

                            <div class="page-header">

                                <button
                                    class="text-button"
                                    on:click=move |_| {
                                        comparison.set(None);
                                    }
                                >
                                    "← Back to Prompt Versions"
                                </button>

                                <h1>
                                    "Compare Prompt Versions"
                                </h1>

                                <p>
                                    {format!(
                                        "{} vs {}",
                                        old_version.version,
                                        new_version.version
                                    )}
                                </p>

                            </div>

                            <div class="prompt-comparison">

                                <div class="comparison-panel">

                                    <div class="comparison-header">

                                        <div>
                                            <h2>
                                                {old_version.version.clone()}
                                            </h2>

                                            <p>
                                                {old_version.description.clone()}
                                            </p>
                                        </div>

                                        <span class="prompt-version-status">
                                            {old_version.status.clone()}
                                        </span>

                                    </div>

                                    <div class="comparison-meta">
                                        {old_version.date.clone()}
                                    </div>

                                    <div class="comparison-content">
                                        {old_version.content.clone()}
                                    </div>

                                </div>


                                <div class="comparison-panel">

                                    <div class="comparison-header">

                                        <div>
                                            <h2>
                                                {new_version.version.clone()}
                                            </h2>

                                            <p>
                                                {new_version.description.clone()}
                                            </p>
                                        </div>

                                        <span class="prompt-version-status">
                                            {new_version.status.clone()}
                                        </span>

                                    </div>

                                    <div class="comparison-meta">
                                        {new_version.date.clone()}
                                    </div>

                                    <div class="comparison-content">
                                        {new_version.content.clone()}
                                    </div>

                                </div>

                            </div>


                            <div class="comparison-summary">

                                <h2>
                                    "Changes"
                                </h2>

                                <div class="change-item">
                                    "+ Improved multilingual classification support"
                                </div>

                                <div class="change-item">
                                    "+ Added more detailed message analysis instructions"
                                </div>

                            </div>

                        </div>

                    });
                }

                if let Some(version) = selected_version.get() {
                    let versions_for_detail_button = versions_for_detail.clone();

                    return Either::Right(Either::Left(view! {

                        <div>

                            <div class="page-header">

                                <button
                                    class="text-button"
                                    on:click=move |_| {
                                        selected_version.set(None);
                                    }
                                >
                                    "← Back to Prompt Versions"
                                </button>

                                <h1>
                                    {version.version.clone()}
                                </h1>

                                <p>
                                    {version.description.clone()}
                                </p>

                            </div>

                            <div class="prompt-detail-card">

                                <div class="prompt-detail-header">

                                    <div>

                                        <h2>
                                            "Prompt"
                                        </h2>

                                        <p class="prompt-version-meta">
                                            {version.date.clone()}
                                        </p>

                                    </div>

                                    <span class="prompt-version-status">
                                        {version.status.clone()}
                                    </span>

                                </div>

                                <div class="prompt-content">
                                    {version.content.clone()}
                                </div>

                                <div class="prompt-detail-actions">

                                    <button
                                        class="text-button"
                                        on:click=move |_| {
                                            selected_version.set(None);
                                        }
                                    >
                                        "BACK"
                                    </button>

                                    <button
                                        class="primary-button"
                                        on:click=move |_| {
                                            comparison.set(
                                                Some((
                                                    versions_for_detail_button[1].clone(),
                                                    version.clone()
                                                ))
                                            );

                                            selected_version.set(None);
                                        }
                                    >
                                        "COMPARE"
                                    </button>

                                </div>

                            </div>

                        </div>

                    }));
                }

                Either::Right(Either::Right(view! {

                    <div>

                        <div class="page-header">

                            <h1>
                                "Prompt Versions"
                            </h1>

                            <p>
                                "Manage and compare versions of your evaluation prompts."
                            </p>

                        </div>

                        <div class="prompts-toolbar">

                            <input
                                class="prompts-search"
                                type="text"
                                placeholder="Search versions..."
                            />

                            <button class="primary-button">
                                "+ New Version"
                            </button>

                        </div>

                        <h2 class="section-title">
                            "Prompt Versions"
                        </h2>

                        <div class="prompt-version-list">

                            {versions_for_list.into_iter().map(|version| {

                                let version_for_view = version.clone();
                                let version_for_compare = version.clone();
                                let versions_for_compare = versions_for_view.clone();

                                view! {

                                    <div class="prompt-version-card">

                                        <div class="prompt-version-top">

                                            <div class="prompt-version-name">
                                                {version.version.clone()}
                                            </div>

                                            <div class="prompt-version-status">
                                                {version.status.clone()}
                                            </div>

                                        </div>

                                        <p class="prompt-version-description">
                                            {version.description.clone()}
                                        </p>

                                        <div class="prompt-version-meta">
                                            {version.date.clone()}
                                        </div>

                                        <div class="prompt-version-actions">

                                            <button
                                                class="text-button"
                                                on:click=move |_| {
                                                    selected_version.set(
                                                        Some(version_for_view.clone())
                                                    );
                                                }
                                            >
                                                "VIEW"
                                            </button>

                                            <button
                                                class="text-button"
                                                on:click=move |_| {

                                                    let old_version =
                                                        if version_for_compare.version == "v2.0" {
                                                            versions_for_compare[1].clone()
                                                        } else {
                                                            versions_for_compare[0].clone()
                                                        };

                                                    comparison.set(
                                                        Some((
                                                            old_version,
                                                            version_for_compare.clone()
                                                        ))
                                                    );
                                                }
                                            >
                                                "COMPARE"
                                            </button>

                                        </div>

                                    </div>

                                }

                            }).collect_view()}

                        </div>

                    </div>

                }))
            }}

        </section>
    }
}