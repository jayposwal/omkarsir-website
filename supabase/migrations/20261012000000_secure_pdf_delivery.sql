-- Secure Razorpay PDF delivery: keep the product files in a PRIVATE Storage bucket.
-- No RLS policies are created for browser roles. Server-side Edge Functions use
-- the Supabase service key, whose value must never be exposed to the browser.

create table if not exists public.pdf_deliveries (
  id uuid primary key default gen_random_uuid(),
  payment_id text not null unique check (payment_id ~ '^pay_[A-Za-z0-9]+$'),
  product_code text not null,
  customer_email text not null,
  amount_paise integer not null check (amount_paise > 0),
  currency text not null check (currency = 'INR'),
  payment_description text not null default '',
  status text not null default 'pending'
    check (status in ('pending', 'sending', 'sent', 'email_failed', 'refunded')),
  expires_at timestamptz not null,
  max_downloads integer not null default 5 check (max_downloads between 1 and 25),
  download_count integer not null default 0 check (download_count >= 0),
  email_attempts integer not null default 0 check (email_attempts >= 0),
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  emailed_at timestamptz,
  last_download_at timestamptz,
  refunded_at timestamptz
);

create index if not exists pdf_deliveries_email_status_idx
  on public.pdf_deliveries (customer_email, status);
create index if not exists pdf_deliveries_expires_at_idx
  on public.pdf_deliveries (expires_at);

alter table public.pdf_deliveries enable row level security;
revoke all on table public.pdf_deliveries from anon, authenticated;
grant all on table public.pdf_deliveries to service_role;

-- Make sure this bucket is PRIVATE. Upload only the exact object keys listed
-- in integrations/supabase-pdf-delivery/README.md.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('private-pdfs', 'private-pdfs', false, 52428800, array['application/pdf'])
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

-- Only one concurrent webhook invocation may claim a pending email. If a
-- function crashes, a retry can reclaim a stale "sending" record after 10 min.
create or replace function public.claim_pdf_delivery_email(p_delivery_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.pdf_deliveries
     set status = 'sending',
         email_attempts = email_attempts + 1,
         last_error = null,
         updated_at = now()
   where id = p_delivery_id
     and (
       status in ('pending', 'email_failed')
       or (status = 'sending' and updated_at < now() - interval '10 minutes')
     );

  return found;
end;
$$;

revoke all on function public.claim_pdf_delivery_email(uuid) from public, anon, authenticated;
grant execute on function public.claim_pdf_delivery_email(uuid) to service_role;

-- Atomically enforce the download count even if a buyer opens the same link in
-- multiple browser tabs at the same time.
create or replace function public.consume_pdf_download(p_delivery_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  claimed_id uuid;
begin
  update public.pdf_deliveries
     set download_count = download_count + 1,
         last_download_at = now(),
         updated_at = now()
   where id = p_delivery_id
     and status = 'sent'
     and expires_at > now()
     and download_count < max_downloads
   returning id into claimed_id;

  return claimed_id is not null;
end;
$$;

revoke all on function public.consume_pdf_download(uuid) from public, anon, authenticated;
grant execute on function public.consume_pdf_download(uuid) to service_role;
