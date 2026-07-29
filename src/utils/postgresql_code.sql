CREATE EXTENSION IF NOT EXISTS citext;
create table Slots (
  slotID uuid primary key default gen_random_uuid(),
  time_start timestamptz not null,
  time_end timestamptz not null,
  occupier_email CITEXT UNIQUE NOT NULL,
  business_id uuid references auth.users(id) on delete cascade not null
);

