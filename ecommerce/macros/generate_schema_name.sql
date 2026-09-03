{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is not none -%}
    {# Remove any prefix that dbt might have added #}
    {%- set schema_parts = custom_schema_name.split('_') -%}
    {%- if schema_parts | length > 1 -%}
      {# If there are multiple parts, take the last one (the custom part) #}
      {{ schema_parts[-1] }}
    {%- else -%}
      {{ custom_schema_name | trim }}
    {%- endif -%}
  {%- else -%}
    {{ target.schema }}
  {%- endif -%}
{%- endmacro %}
