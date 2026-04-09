pub trait Validate {
    fn validate(&self) -> Result<(), String>;
}

pub trait StableHash {
    fn stable_hash(&self) -> String;
}

pub trait KernelStage {
    fn stage_name(&self) -> &'static str;
}
