use std::{env, io, net::SocketAddr};

use actix_web::{App, HttpServer};

#[actix_web::main]
async fn main() -> io::Result<()> {
    let address = env::var_os("EMBERLINE_BIND_ADDR")
        .unwrap_or_else(|| "127.0.0.1:8000".into())
        .to_str()
        .and_then(|value| value.parse::<SocketAddr>().ok())
        .ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidInput,
                "EMBERLINE_BIND_ADDR must be an IP:port socket address",
            )
        })?;

    let server =
        HttpServer::new(|| App::new().configure(emberline_api::configure)).bind(address)?;
    println!("EmberLine API listening on http://{address}");
    server.run().await
}
