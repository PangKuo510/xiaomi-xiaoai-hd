//! HD-specific, read-only RPC dispatcher. No dependency on upstream device handlers.
use serde_json::{json, Value};
use std::io::Read;
use std::process::Stdio;
use std::time::Duration;
use tokio::io::AsyncReadExt;

pub const COMMANDS: [&str; 3] = ["get_version", "get_model", "get_status"];
pub const LIMIT: usize = 8192;

pub fn firmware_option(text: &str, key: &str) -> Option<String> {
    text.lines().find_map(|line| {
        let words: Vec<_> = line.split_whitespace().collect();
        if words.len() == 3 && words[0] == "option" && words[1] == key {
            let value = words[2].trim_matches(['\'', '"']);
            if !value.is_empty() && value.len() <= 64 && value.bytes().all(|c| c.is_ascii_alphanumeric() || b"._-".contains(&c)) {
                return Some(value.to_owned());
            }
        }
        None
    })
}

pub fn identify(text: &str) -> Result<Value, &'static str> {
    if firmware_option(text, "HARDWARE").as_deref() != Some("M01") {
        return Err("unsupported_model");
    }
    Ok(json!({"model":"XMYX01JY", "hardware":"M01"}))
}

pub fn memory(text: &str) -> Value {
    let mut out = serde_json::Map::new();
    for (field, name) in [("MemTotal:", "total_kib"), ("MemAvailable:", "available_kib")] {
        if let Some(value) = text.lines().find_map(|line| {
            let fields: Vec<_> = line.split_whitespace().collect();
            (fields.len() == 3 && fields[0] == field && fields[2] == "kB")
                .then(|| fields[1].parse::<u64>().ok()).flatten()
        }) {
            out.insert(name.into(), json!(value));
        }
    }
    Value::Object(out)
}

pub fn player(text: &str) -> Result<Value, &'static str> {
    let outer: Value = serde_json::from_str(text).map_err(|_| "invalid_player_response")?;
    if outer.get("code").and_then(Value::as_i64) != Some(0) {
        return Err("player_query_failed");
    }
    let info: Value = match outer.get("info") {
        Some(Value::String(s)) => serde_json::from_str(s).map_err(|_| "invalid_player_response")?,
        Some(Value::Object(o)) => Value::Object(o.clone()),
        _ => return Err("invalid_player_response"),
    };
    // Explicit projection: never return URLs, content, serials, tokens or raw output.
    let mut out = serde_json::Map::new();
    for key in ["status", "volume", "loop_type"] {
        if let Some(n) = info.get(key).and_then(Value::as_i64) {
            if (0..=255).contains(&n) {
                out.insert(key.into(), json!(n));
            }
        }
    }
    if out.is_empty() { return Err("invalid_player_response"); }
    Ok(Value::Object(out))
}

fn read_fixed(path: &str) -> Result<String, &'static str> {
    // No caller-supplied paths. An exact fixed-path allowlist is enforced here too.
    if !["/usr/share/mico/version", "/proc/meminfo", "/proc/uptime"].contains(&path) {
        return Err("path_not_allowed");
    }
    let file = std::fs::File::open(path).map_err(|_| "read_unavailable")?;
    let mut text = String::new();
    file.take((LIMIT + 1) as u64).read_to_string(&mut text).map_err(|_| "read_unavailable")?;
    if text.len() > LIMIT { return Err("read_too_large"); }
    Ok(text)
}

async fn query_player() -> Result<Value, &'static str> {
    // Fixed argv, absolute binary path, no shell and no RPC-provided arguments.
    let mut child = tokio::process::Command::new("/bin/ubus")
        .args(["-t", "2", "call", "mediaplayer", "player_get_play_status", "{}"])
        .stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::null())
        .kill_on_drop(true).spawn().map_err(|_| "player_unavailable")?;
    let stdout = child.stdout.take().ok_or("player_unavailable")?;
    let result = tokio::time::timeout(Duration::from_secs(3), async {
        let mut output = String::new();
        stdout.take(4097).read_to_string(&mut output).await.map_err(|_| "player_unavailable")?;
        if output.len() > 4096 { return Err("player_response_too_large"); }
        if !child.wait().await.map_err(|_| "player_unavailable")?.success() {
            return Err("player_unavailable");
        }
        player(&output)
    }).await;
    match result {
        Ok(value) => value,
        Err(_) => Err("player_timeout"),
    }
}

async fn query(command: &str, mock: bool) -> Result<Value, &'static str> {
    let version = if mock {
        "option ROM 'test-version'\noption HARDWARE 'M01'".to_owned()
    } else { read_fixed("/usr/share/mico/version")? };
    identify(&version)?; // Fail closed on Pro/LX06 or an unknown device.
    match command {
        "get_version" => Ok(json!({"client":"hd-handshake", "version":env!("CARGO_PKG_VERSION"),
            "protocol":1, "firmware":firmware_option(&version,"ROM"), "simulated":mock})),
        "get_model" => identify(&version),
        "get_status" => {
            let (mem, uptime, playback) = if mock {
                ("MemTotal: 200000 kB\nMemAvailable: 90000 kB".into(), "123.5 400.0".into(),
                 Ok(json!({"status":0,"volume":30,"loop_type":1})))
            } else {
                (read_fixed("/proc/meminfo")?, read_fixed("/proc/uptime")?, query_player().await)
            };
            let seconds = uptime.split_whitespace().next().and_then(|s| s.parse::<f64>().ok())
                .filter(|n| n.is_finite() && *n >= 0.0);
            let mut data = json!({"read_only":true, "simulated":mock, "memory":memory(&mem),
                "uptime_seconds":seconds, "commands":COMMANDS});
            match playback {
                Ok(value) => data["player"] = value,
                Err(reason) => data["player_error"] = json!(reason),
            }
            Ok(data)
        }
        _ => Err("command_not_allowed"),
    }
}

fn error(id: &str, reason: &str) -> Value {
    json!({"Response":{"id":id,"code":-1,"msg":reason}})
}

pub async fn dispatch(text: &str, mock: bool) -> Value {
    if text.len() > LIMIT { return error("", "message_too_large"); }
    let Ok(value) = serde_json::from_str::<Value>(text) else { return error("", "invalid_request"); };
    let Some(envelope) = value.as_object() else { return error("", "invalid_request"); };
    if envelope.len() != 1 { return error("", "invalid_request"); }
    let Some(request) = envelope.get("Request").and_then(Value::as_object) else { return error("", "invalid_request"); };
    let Some(id) = request.get("id").and_then(Value::as_str).filter(|id|
        !id.is_empty() && id.len() <= 64 && id.bytes().all(|c| c.is_ascii_alphanumeric() || b"-_".contains(&c)))
    else { return error("", "invalid_request"); };
    if request.keys().any(|k| !["id", "command", "payload"].contains(&k.as_str())) {
        return error(id, "invalid_request");
    }
    if request.get("payload").is_some_and(|p| !p.is_null()) { return error(id, "payload_not_allowed"); }
    let Some(command) = request.get("command").and_then(Value::as_str) else { return error(id,"invalid_request"); };
    if !COMMANDS.contains(&command) { return error(id,"command_not_allowed"); }
    match query(command, mock).await {
        Ok(data) => json!({"Response":{"id":id,"code":0,"data":data}}),
        Err(reason) => error(id,reason),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn model_fails_closed_and_identity_is_projected() {
        assert!(identify("option HARDWARE 'LX06'").is_err());
        assert!(identify("option HARDWARE 'M01extra'").is_err());
        assert!(identify("").is_err());
        assert_eq!(identify("option HARDWARE 'M01'\noption SN 'not-for-output'").unwrap(),
            json!({"model":"XMYX01JY","hardware":"M01"}));
    }
    #[test]
    fn status_filters_private_fields_and_invalid_responses() {
        assert_eq!(player(r#"{"code":0,"info":{"status":0,"volume":30,"token":"not-for-output","url":"not-for-output"}}"#).unwrap(), json!({"status":0,"volume":30}));
        assert_eq!(player(r#"{"code":0,"info":"{\"volume\":30}"}"#).unwrap(), json!({"volume":30}));
        assert!(player(r#"{"code":1,"info":{"volume":30}}"#).is_err());
        assert!(player(r#"{"code":0,"info":{"volume":-1}}"#).is_err());
        assert!(player("invalid").is_err());
    }
    #[tokio::test]
    async fn forbidden_commands_and_payloads_do_not_touch_system_backend() {
        for cmd in ["run_shell","start_play","start_recording","set_boot","mic_on","unknown"] {
            let response = dispatch(&json!({"Request":{"id":"t","command":cmd,"payload":null}}).to_string(),false).await;
            assert_eq!(response["Response"]["msg"],"command_not_allowed");
        }
        let response = dispatch(r#"{"Request":{"id":"t","command":"get_status","payload":{"shell":"anything"}}}"#,false).await;
        assert_eq!(response["Response"]["msg"],"payload_not_allowed");
    }
    #[tokio::test]
    async fn malformed_envelopes_and_limits() {
        for input in ["broken", "[]", r#"{"Event":{}}"#, r#"{"Request":{"id":"","command":"get_status"}}"#,
            r#"{"Request":{"id":"t","command":"get_status","extra":1}}"#] {
            assert_eq!(dispatch(input,true).await["Response"]["code"],-1);
        }
        assert_eq!(dispatch(&"x".repeat(LIMIT+1),true).await["Response"]["msg"],"message_too_large");
    }
    #[tokio::test]
    async fn all_three_mock_queries_are_explicitly_simulated() {
        for cmd in COMMANDS {
            let response = dispatch(&json!({"Request":{"id":"test","command":cmd,"payload":null}}).to_string(),true).await;
            assert_eq!(response["Response"]["id"],"test");
            assert_eq!(response["Response"]["code"],0);
        }
    }
    #[test]
    fn memory_only_exposes_allowed_numeric_fields() {
        assert_eq!(memory("MemTotal: 123 kB\nToken: 99 kB\nMemAvailable: invalid kB"),json!({"total_kib":123}));
        assert!(read_fixed("/etc/shadow").is_err());
    }
}
