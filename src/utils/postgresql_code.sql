CREATE EXTENSION IF NOT EXISTS citext;
create table Slots (
  slotID uuid primary key default gen_random_uuid(),
  time_start timestamptz not null,
  time_end timestamptz not null,
  occupier_email CITEXT UNIQUE NOT NULL,
  business_id uuid references auth.users(id) on delete cascade not null
);

-- anon, authenticated code which i entered when the supabase tool execution was giving an error:
grant usage on schema public to anon, authenticated;

grant select on table public.slots to anon, authenticated;
grant insert, update on table public.slots to authenticated;

-- if you use serial/identity ids
grant usage, select on all sequences in schema public to authenticated;

create policy "slots_read"
on public.slots
for select
to anon, authenticated
using (true);

create policy "slots_book_own"
on public.slots
for update
to authenticated
using (auth.uid() = business_id or business_id is null)
with check (auth.uid() = business_id);

create policy "slots_insert"
on public.slots
for insert
to authenticated
with check (auth.uid() = business_id);

    -- DELETE policy  
create policy "slots_delete"
on public.slots
for delete
to authenticated
using (auth.uid() = business_id);
