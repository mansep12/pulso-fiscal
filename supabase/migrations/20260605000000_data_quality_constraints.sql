-- Refuerza invariantes de calidad de datos sin reabrir permisos publicos.
--
-- Las constraints se agregan como NOT VALID para no bloquear instancias que ya
-- tengan datos historicos cargados manualmente. PostgreSQL igualmente las exige
-- para filas nuevas o actualizadas.

-- ============================================================
-- dataset_runs
-- ============================================================
do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_dataset_not_blank') then
        alter table dataset_runs add constraint chk_dataset_runs_dataset_not_blank
        check (btrim(dataset) <> '') not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_run_id_not_blank') then
        alter table dataset_runs add constraint chk_dataset_runs_run_id_not_blank
        check (btrim(run_id) <> '') not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_period_format') then
        alter table dataset_runs add constraint chk_dataset_runs_period_format
        check (
            period_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'
            and period_to ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'
        ) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_period_order') then
        alter table dataset_runs add constraint chk_dataset_runs_period_order
        check (period_from <= period_to) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_row_count_non_negative') then
        alter table dataset_runs add constraint chk_dataset_runs_row_count_non_negative
        check (row_count >= 0) not valid;
    end if;
end $$;

-- ============================================================
-- senado_gastos_operacionales
-- ============================================================
do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_periodo_format') then
        alter table senado_gastos_operacionales add constraint chk_sgo_periodo_format
        check (periodo is null or periodo = '' or periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$') not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_mes_range') then
        alter table senado_gastos_operacionales add constraint chk_sgo_mes_range
        check (mes is null or mes between 1 and 12) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_periodo_consistency') then
        alter table senado_gastos_operacionales add constraint chk_sgo_periodo_consistency
        check (
            periodo is null
            or periodo = ''
            or ano is null
            or mes is null
            or periodo = ano::text || '-' || lpad(mes::text, 2, '0')
        ) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_row_number_positive') then
        alter table senado_gastos_operacionales add constraint chk_sgo_row_number_positive
        check (row_number is null or row_number > 0) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_row_status_allowed') then
        alter table senado_gastos_operacionales add constraint chk_sgo_row_status_allowed
        check (
            row_status is not null
            and row_status in (
                'ok',
                'ajuste',
                'duplicado',
                'monto_en_texto',
                'nota',
                'sin_categoria',
                'sin_monto'
            )
        ) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_include_status_consistency') then
        alter table senado_gastos_operacionales add constraint chk_sgo_include_status_consistency
        check (
            (include_in_ranking = true and row_status = 'ok')
            or (include_in_ranking = false and row_status <> 'ok')
        ) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_ranked_fields_present') then
        alter table senado_gastos_operacionales add constraint chk_sgo_ranked_fields_present
        check (
            include_in_ranking = false
            or (
                periodo is not null and periodo <> ''
                and parlamentario_id is not null and parlamentario_id <> ''
                and categoria_id is not null and categoria_id <> ''
                and monto is not null
            )
        ) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgo_traceability_present') then
        alter table senado_gastos_operacionales add constraint chk_sgo_traceability_present
        check (
            btrim(source_url) <> ''
            and btrim(raw_file) <> ''
            and btrim(raw_body_sha256) <> ''
            and btrim(fecha_captura_utc) <> ''
        ) not valid;
    end if;
end $$;

create unique index if not exists uq_sgo_run_row_number
on senado_gastos_operacionales (run_id, row_number)
where row_number is not null;

create unique index if not exists uq_sgo_ranked_source
on senado_gastos_operacionales (run_id, source_id)
where include_in_ranking = true and source_id is not null and source_id <> '';

-- ============================================================
-- senado_gastos_operacionales_ranking
-- ============================================================
do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'chk_sgor_periodo_format') then
        alter table senado_gastos_operacionales_ranking add constraint chk_sgor_periodo_format
        check (periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$') not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgor_mes_range') then
        alter table senado_gastos_operacionales_ranking add constraint chk_sgor_mes_range
        check (mes between 1 and 12) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgor_periodo_consistency') then
        alter table senado_gastos_operacionales_ranking add constraint chk_sgor_periodo_consistency
        check (periodo = ano::text || '-' || lpad(mes::text, 2, '0')) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgor_rank_positive') then
        alter table senado_gastos_operacionales_ranking add constraint chk_sgor_rank_positive
        check (rank > 0) not valid;
    end if;

    if not exists (select 1 from pg_constraint where conname = 'chk_sgor_totals_consistent') then
        alter table senado_gastos_operacionales_ranking add constraint chk_sgor_totals_consistent
        check (
            total_monto >= 0
            and registros > 0
            and total_ajustes <= 0
            and registros_ajuste >= 0
            and registros_sin_monto >= 0
            and registros_excluidos >= 0
        ) not valid;
    end if;
end $$;

create unique index if not exists uq_sgor_identity
on senado_gastos_operacionales_ranking (run_id, periodo, categoria_id, parlamentario_id);

create unique index if not exists uq_sgor_rank
on senado_gastos_operacionales_ranking (run_id, periodo, categoria_id, rank);
