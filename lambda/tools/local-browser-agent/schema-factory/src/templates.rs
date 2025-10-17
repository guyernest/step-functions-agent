use handlebars::Handlebars;
use serde_json::json;

use crate::schema::CanonicalSchema;

/// Template generator for creating artifacts from canonical schema
pub struct TemplateGenerator {
    handlebars: Handlebars<'static>,
}

impl TemplateGenerator {
    pub fn new() -> Self {
        let mut handlebars = Handlebars::new();

        // Register templates
        Self::register_templates(&mut handlebars);

        Self { handlebars }
    }

    fn register_templates(handlebars: &mut Handlebars) {
        // CDK Stack template
        handlebars
            .register_template_string("cdk_stack", include_str!("../templates/cdk_stack.py.hbs"))
            .expect("Failed to register cdk_stack template");

        // Browser script template
        handlebars
            .register_template_string("browser_script", include_str!("../templates/browser_script.json.hbs"))
            .expect("Failed to register browser_script template");

        // Tool specification template
        handlebars
            .register_template_string("tool_spec", include_str!("../templates/tool_spec.json.hbs"))
            .expect("Failed to register tool_spec template");

        // Output tool specification template
        handlebars
            .register_template_string("output_tool_spec", include_str!("../templates/output_tool_spec.json.hbs"))
            .expect("Failed to register output_tool_spec template");

        // Batch mapping template
        handlebars
            .register_template_string("batch_mapping", include_str!("../templates/batch_mapping.json.hbs"))
            .expect("Failed to register batch_mapping template");

        // Validator template
        handlebars
            .register_template_string("validator", include_str!("../templates/validator.py.hbs"))
            .expect("Failed to register validator template");
    }

    pub fn generate_cdk_stack(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("cdk_stack", &data)?;
        Ok(rendered)
    }

    pub fn generate_browser_script(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("browser_script", &data)?;
        Ok(rendered)
    }

    pub fn generate_tool_spec(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("tool_spec", &data)?;
        Ok(rendered)
    }

    pub fn generate_output_tool_spec(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("output_tool_spec", &data)?;
        Ok(rendered)
    }

    pub fn generate_batch_mapping(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("batch_mapping", &data)?;
        Ok(rendered)
    }

    pub fn generate_validator(&self, schema: &CanonicalSchema) -> anyhow::Result<String> {
        let data = self.prepare_template_data(schema);
        let rendered = self.handlebars.render("validator", &data)?;
        Ok(rendered)
    }

    fn prepare_template_data(&self, schema: &CanonicalSchema) -> serde_json::Value {
        json!({
            "schema_id": schema.schema_id(),
            "extraction_name": schema.extraction_name,
            "version": schema.version,
            "description": schema.description,
            "tool_name": schema.tool_name(),
            "agent_name": schema.agent_name(),
            "input_schema": schema.input_schema,
            "output_schema": schema.output_schema,
            "browser_config": schema.browser_config,
            "metadata": schema.metadata,
            "required_input_fields": schema.required_input_fields(),
            "required_output_fields": schema.required_output_fields(),
        })
    }
}

impl Default for TemplateGenerator {
    fn default() -> Self {
        Self::new()
    }
}
