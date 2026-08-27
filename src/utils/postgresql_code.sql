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

-- Database function

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function initialize_pinecone_data();

create function initialize_pinecone_data()
returns trigger
language plpgsql
as $$
begin
  insert into pinecone_data_table(namespace_name, business_id)
  values (NEW.email, NEW.id);
  return NEW;
end;
$$;

create policy "read_namespace_name"
on public.pinecone_data_table
for select
to authenticated
using (true);

grant select on table public.pinecone_data_table to anon, authenticated;


grant select, insert, update, delete on public.links to authenticated;

create policy "read_link_data"
on public.links 
for select 
to authenticated
using (auth.uid() = business_id)

alter table public.pinecone_data_table 
enable row level security;

alter table public.links
enable row level security;

---create policy "read_link_data"
---on public.links
---for select, insert, update
---to authenticated  
---using (auth.uid() = business_id);

create or replace function initialize_default_link()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  chars text[] := '{0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z}';
  result text := '';
  i integer := 0;

begin
  for i in 1..8 loop
    result := result || chars[1+random()*(array_length(chars, 1)-1)];
  end loop;

  insert into public.links(url, business_id)
  values(result, new.id);
  return new; 
end;
$$;

create trigger on_auth_user_created_two
after insert on auth.users
for each row
execute function initialize_default_link();

create policy "link_policies_select"
on public.links
for select
to authenticated 
using (auth.uid() = business_id);

create policy "link_policies_insert"
on public.links
for insert
to authenticated 
with check ((select auth.uid()) = business_id);

CREATE POLICY "link_policies_update" 
ON public.links 
FOR UPDATE 
TO authenticated 
USING ((select auth.uid()) = business_id)
WITH CHECK ((select auth.uid()) = business_id);

create policy "link_policies_delete"
on public.links
for delete
to authenticated 
using (auth.uid() = business_id);

grant select on table public.links to anon;

create policy "anon_get_business_id_from_urlstring"
on public.links 
for select
to anon
using (true)

grant select(namespace_name, business_id) on table public.pinecone_data_table to anon;

grant select on table public.slots to anon;


create policy "namespace_anon_allow_throught_businessID"
on public.pinecone_data_table
for select
to anon     
using (true);

create policy "read_slots_anon"
on public.slots
for select
to anon
using (true);

grant insert on table public.slots to anon; 

create policy "allow_creating_slot"
on public.slots
for insert
to anon
with check(true);

alter table public.slots
add column status text check (status in ('pending', 'confirmed')),
add column verification_id uuid default gen_random_uuid();

-- create a database function -> takes in verification_id -> sets 
-- some are missing
alter table public.ingestions
add column record_ids_json jsonb;

grant insert on table public.ingestions to authenticated;

create policy "insert_ingestion_for_authenticated"
on public.ingestions
for insert
to authenticated
with check (auth.uid()=business_id);

-- postgrest asks for the inserted row back (Prefer: return=representation), so the
-- insert alone is not enough - without select it fails 42501 permission denied
grant select on table public.ingestions to authenticated;

create policy "select_own_ingestions"
on public.ingestions
for select
to authenticated
using (auth.uid()=business_id);
