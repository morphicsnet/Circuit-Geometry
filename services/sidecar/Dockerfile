FROM rust:1.81 as build
WORKDIR /app
COPY . .
RUN cargo build --release -p geoclt-cli

FROM debian:bookworm-slim
COPY --from=build /app/target/release/geoclt-cli /usr/local/bin/geoclt-cli
CMD ["geoclt-cli", "version"]
