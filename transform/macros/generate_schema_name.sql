{# 커스텀 스키마명을 그대로 쓴다 — 기본 동작(<target>_<custom> 접합)을 끄고
   +schema: slv/gld/sbx 가 실제 스키마로 직결되게 한다 (→ design/10). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
