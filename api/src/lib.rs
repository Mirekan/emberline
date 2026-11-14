mod routes;

use actix_web::web;
use routes::{fake_not_found, health};

// ? This function will be used for configuring how the server will use all of the routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.route("/api/health", web::get().to(health))
        .default_service(web::to(fake_not_found));
}

// ? This function will be called for testing (cargo test)
#[cfg(test)]
mod tests {
    use actix_web::{App, http::StatusCode, test};
    use serde_json::{Value, json};

    /* ? This is the first test, it will check if the server
     * can receive and give back a response to the client with
     * the correct data and header
     * */
    #[actix_web::test]
    async fn health_reports_liveness_without_claiming_data_readiness() {
        let app = test::init_service(App::new().configure(super::configure)).await;
        let response = test::call_service(
            &app,
            test::TestRequest::get().uri("/api/health").to_request(),
        )
        .await;

        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(
            response.headers().get("content-type").unwrap(),
            "application/json"
        );
        assert!(
            !response
                .headers()
                .contains_key("access-control-allow-origin")
        );
        let body: Value = test::read_body_json(response).await;
        assert_eq!(
            body,
            json!({
                "service": "emberline-api",
                "version": env!("CARGO_PKG_VERSION"),
                "status": "not_ready",
                "ready": false,
                "data_version": null,
                "run_id": null
            })
        );
    }

    /* ? This is the second test, it will check if the server
     * can receive and give back a response to the client a
     * data if the client look for something that isn't in the
     * registered routes.
     * */
    #[actix_web::test]
    async fn unknown_routes_return_fake_online_route() {
        let app = test::init_service(App::new().configure(super::configure)).await;
        let response = test::call_service(
            &app,
            test::TestRequest::get()
                .uri("/not-implemented?input=do-not-reflect") // ? Check on random, unknown routes
                .to_request(),
        )
        .await;

        assert_ne!(response.status(), StatusCode::NOT_FOUND);

        let body: Value = test::read_body_json(response).await;
        assert!(body.get("data").is_some());
    }
}
