use actix_web::HttpResponse;
use rand::Rng;
use serde_json::json;

// ? This function is used to check the health of the backend server
pub async fn health() -> HttpResponse {
    // ponytail: liveness only; derive readiness and run IDs once validated artifacts are wired.
    HttpResponse::Ok().json(json!({
        "service": "emberline-api",
        "version": env!("CARGO_PKG_VERSION"),
        "status": "not_ready",
        "ready": false,
        "data_version": null,
        "run_id": null
    }))
}

// ? This route will act as a fake found page to make it harder for hacker to do web discovery to us.
pub async fn fake_not_found() -> HttpResponse {
    let mut rng = rand::rng();

    // ? Generate a random number for the size of the packet data
    let r: usize = rng.random_range(0..=255);
    let data: Vec<u8> = vec![0; r];

    // ?  Returns back the data
    HttpResponse::Ok()
        .content_type("application/json")
        .json(json!({
            "data": data
        }))
}
