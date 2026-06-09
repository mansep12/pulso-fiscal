-- Backstop de DB: un run publicado no puede quedar sin manifest publico.

do $$
begin
    if not exists (select 1 from pg_constraint where conname = 'chk_dataset_runs_ok_manifest_public') then
        alter table dataset_runs add constraint chk_dataset_runs_ok_manifest_public
        check (
            status <> 'ok'
            or (
                btrim(manifest_r2_key) ~ '^senado/gastos_operacionales/runs/[^/]+/pipeline_manifest[.]json$'
                and btrim(public_manifest_url) ~ '^https://[^[:space:]]+/senado/gastos_operacionales/runs/[^/]+/pipeline_manifest[.]json$'
            )
        ) not valid;
    end if;
end $$;
