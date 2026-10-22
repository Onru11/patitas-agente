-- =====================================================================
-- Patitaspe — Esquema de captura (Supabase / Postgres)
-- Cómo usarlo: Supabase → SQL Editor → New query → pega TODO esto → Run.
-- Seguro de correr varias veces (usa IF NOT EXISTS / OR REPLACE).
-- =====================================================================

-- 1) TABLA append-only de eventos. Cada interacción de la web = una fila.
create table if not exists public.eventos (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  tipo        text,        -- calculo | verificacion | triaje | cartilla | lead | plan
  email       text,        -- correo si lo dejó (null si fue anónimo)
  monto       numeric,     -- monto dispuesto / cotizado
  tier        text,        -- plan elegido (básico / emergencias / total)
  zona        text,        -- zona o distrito declarado
  mascota     text,        -- perro / gato / especie
  veredicto   text,        -- resultado del verificador / triaje
  nivel       text,        -- nivel de triaje
  origen      text,        -- atribución de campaña / canal (UTM, referrer)
  data        jsonb        -- payload COMPLETO (todo lo demás; a prueba de futuro)
);

create index if not exists eventos_created_idx on public.eventos (created_at desc);
create index if not exists eventos_tipo_idx    on public.eventos (tipo);
create index if not exists eventos_email_idx   on public.eventos (email) where email is not null;
create index if not exists eventos_zona_idx    on public.eventos (zona);

-- 2) SEGURIDAD (RLS): el público SOLO puede INSERTAR. Nadie anónimo puede leer.
alter table public.eventos enable row level security;

grant usage on schema public to anon;
grant insert on table public.eventos to anon;

drop policy if exists "anon puede insertar eventos" on public.eventos;
create policy "anon puede insertar eventos"
  on public.eventos for insert
  to anon
  with check (true);

-- (La lectura queda solo para el dashboard de Supabase / service_role / usuarios
--  autenticados. El público NO puede listar ni descargar la data.)

-- 3) VISTA de CONTACTOS deduplicados por correo. Esta vista ES tu activo (la lista).
create or replace view public.contactos as
select
  email,
  min(created_at)                                  as primer_contacto,
  max(created_at)                                  as ultimo_contacto,
  count(*)                                         as eventos,
  max(zona)    filter (where zona    is not null)  as zona,
  max(mascota) filter (where mascota is not null)  as mascota,
  max(tier)    filter (where tier    is not null)  as ultimo_tier,
  max(monto)                                       as monto_max,
  array_agg(distinct tipo)                         as acciones,
  bool_or(tipo = 'plan')                           as mostro_interes_plan,
  max(origen)  filter (where origen  is not null)  as origen
from public.eventos
where email is not null and email <> ''
group by email
order by ultimo_contacto desc;

-- 4) VISTA de EMBUDO: cuántos de cada tipo y qué % dejó correo (tu KPI del modelo B).
create or replace view public.embudo as
select
  tipo,
  count(*)                                    as total,
  count(*) filter (where email is not null)   as con_correo,
  round(100.0 * count(*) filter (where email is not null) / nullif(count(*),0), 1) as pct_captura
from public.eventos
group by tipo
order by total desc;

-- 5) Blindaje de PII: que las vistas NO sean accesibles por el público vía API.
revoke all on public.contactos from anon, authenticated;
revoke all on public.embudo    from anon, authenticated;

-- Listo. Consultas útiles (corre en el SQL Editor cuando quieras):
--   select * from public.contactos;                       -- tu lista de correos
--   select * from public.embudo;                          -- conversión por herramienta
--   select count(*) from public.eventos;                  -- total de interacciones
--   select zona, count(*) from public.eventos group by zona order by 2 desc;  -- dónde hay demanda
