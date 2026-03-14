use jsonschema::JSONSchema;
use std::path::Path;

pub fn validate_json_against_schema(instance: &str, schema: &str) -> Result<(), String> {
    let instance_json: serde_json::Value =
        serde_json::from_str(instance).map_err(|error| format!("invalid instance JSON: {error}"))?;
    let schema_json: serde_json::Value =
        serde_json::from_str(schema).map_err(|error| format!("invalid schema JSON: {error}"))?;

    let compiled = JSONSchema::options()
        .compile(&schema_json)
        .map_err(|error| format!("schema compilation error: {error}"))?;

    if let Err(errors) = compiled.validate(&instance_json) {
        let details = errors
            .map(|error| error.to_string())
            .collect::<Vec<_>>()
            .join("; ");
        return Err(format!("schema validation failed: {details}"));
    }

    Ok(())
}

pub fn validate_file_against_schema_path<P: AsRef<Path>, Q: AsRef<Path>>(
    instance_path: P,
    schema_path: Q,
) -> Result<(), String> {
    let instance = std::fs::read_to_string(instance_path.as_ref())
        .map_err(|error| format!("failed to read instance file: {error}"))?;
    let schema = std::fs::read_to_string(schema_path.as_ref())
        .map_err(|error| format!("failed to read schema file: {error}"))?;
    validate_json_against_schema(&instance, &schema)
}

#[cfg(test)]
mod tests {
    use super::validate_json_against_schema;

    #[test]
    fn validates_matching_shape() {
        let schema = r#"{
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "required": ["name"],
          "properties": { "name": { "type": "string" } }
        }"#;
        let instance = r#"{ "name": "geoclt" }"#;
        assert!(validate_json_against_schema(instance, schema).is_ok());
    }

    #[test]
    fn rejects_missing_required_fields() {
        let schema = r#"{
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "required": ["name"],
          "properties": { "name": { "type": "string" } }
        }"#;
        let instance = r#"{ "missing": true }"#;
        assert!(validate_json_against_schema(instance, schema).is_err());
    }
}
