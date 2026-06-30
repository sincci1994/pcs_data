{#
  +schema 값을 접두 없이 '그대로' Oracle 스키마(=유저)명으로 사용.
  (기본 dbt 동작은 <target_schema>_<custom> 으로 합쳐버리므로 override)
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
