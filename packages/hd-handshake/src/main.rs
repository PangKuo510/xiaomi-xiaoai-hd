use futures_util::{SinkExt, StreamExt};
use hd_handshake::{dispatch, LIMIT};
use std::time::Duration;
use tokio_tungstenite::{connect_async_with_config, tungstenite::{Message, protocol::WebSocketConfig}};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut server = "ws://127.0.0.1:4399".to_owned();
    let mut mock = false;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--mock" => mock = true,
            "--server" if i + 1 < args.len() => { i += 1; server = args[i].clone(); },
            _ => return Err("usage: hd-handshake [--mock] [--server ws://127.0.0.1:4399]".into()),
        }
        i += 1;
    }
    // First version deliberately permits loopback only. LAN deployment isn't enabled.
    let Some(port) = server.strip_prefix("ws://127.0.0.1:").and_then(|s| s.parse::<u16>().ok()).filter(|p| *p > 0)
    else { return Err("only numeric loopback WebSocket endpoints are supported".into()); };
    let endpoint = format!("ws://127.0.0.1:{port}");
    let config = WebSocketConfig::default().max_message_size(Some(LIMIT)).max_frame_size(Some(LIMIT));
    let (mut ws, _) = tokio::time::timeout(Duration::from_secs(5), connect_async_with_config(endpoint,Some(config),false)).await??;
    // No startup commands, events, audio or reconnect loop. At most 16 requests/session.
    for _ in 0..16 {
        let frame = tokio::time::timeout(Duration::from_secs(10),ws.next()).await?;
        match frame {
            Some(Ok(Message::Text(text))) => {
                let response = dispatch(text.as_str(),mock).await;
                ws.send(Message::Text(response.to_string().into())).await?;
            }
            Some(Ok(Message::Close(_))) | None => { let _ = ws.close(None).await; return Ok(()); },
            Some(Ok(Message::Ping(_))) | Some(Ok(Message::Pong(_))) => {},
            _ => { let _ = ws.close(None).await; return Err("unsupported frame".into()); },
        }
    }
    ws.close(None).await?;
    Ok(())
}
