{#
  on-run-end 훅: dbt 실행 결과를 PCS_CTL 에 적재 (Elementary 대체, Oracle 네이티브).
  - 모델/seed/snapshot → PCS_CTL.C_JOB_RUN (status, 소요시간, 적재행수)
  - test                → PCS_CTL.A_DQ_RESULT (pass/fail, 메시지)
  Cosmos 는 모델마다 별도 dbt invocation 으로 실행하므로 노드별 timing 이 자연히 분리 적재됨.
#}
{% macro log_run_results_to_ctl() %}
  {% if execute and results %}
    {% for res in results %}
      {% set node = res.node %}
      {% set rtype = node.resource_type %}

      {% if rtype in ['model', 'seed', 'snapshot'] %}
        {% set rows = 0 %}
        {% if res.adapter_response and res.adapter_response.get('rows_affected') is not none %}
          {% set rows = res.adapter_response.get('rows_affected') %}
        {% endif %}
        {% set exec_sec = res.execution_time | default(0) | round(3) %}
        {% set ins %}
          INSERT INTO PCS_CTL.C_JOB_RUN (RUN_ID, DAG_ID, TASK_ID, STATE, START_TS, END_TS, ROW_CNT)
          VALUES ('{{ invocation_id }}', 'dbt', '{{ node.name }}', '{{ res.status }}',
                  SYSTIMESTAMP - NUMTODSINTERVAL({{ exec_sec }}, 'SECOND'),
                  SYSTIMESTAMP, {{ rows }})
        {% endset %}
        {% do run_query(ins) %}

      {% elif rtype == 'test' %}
        {% set passyn = 'Y' if res.status == 'pass' else 'N' %}
        {% set msg = (res.message | default('') | string | replace("'", "")) %}
        {% set ins2 %}
          INSERT INTO PCS_CTL.A_DQ_RESULT (RUN_ID, CHECK_NM, PASS_YN, DETAIL)
          VALUES ('{{ invocation_id }}', '{{ node.name }}', '{{ passyn }}', '{{ msg[:900] }}')
        {% endset %}
        {% do run_query(ins2) %}
      {% endif %}
    {% endfor %}
    {# dbt-oracle 은 on-run-end DML 을 자동 커밋하지 않으므로 명시적 COMMIT 필요 #}
    {% do run_query('COMMIT') %}
    {% do log("[CTL] logged " ~ results | length ~ " dbt node result(s)", info=true) %}
  {% endif %}
{% endmacro %}
