CREATE TABLE public.leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  public_id text NOT NULL UNIQUE DEFAULT ('KDR-' || upper(substring(replace(gen_random_uuid()::text, '-', '') from 1 for 10))),
  submission_key uuid NOT NULL UNIQUE,
  name text NOT NULL CHECK (char_length(name) BETWEEN 2 AND 80),
  email text NOT NULL CHECK (char_length(email) BETWEEN 5 AND 254),
  phone text CHECK (phone IS NULL OR char_length(phone) <= 40),
  company text CHECK (company IS NULL OR char_length(company) <= 120),
  service text NOT NULL CHECK (service IN ('business-site', 'landing-page', 'online-store', 'custom-development', 'unsure', 'contact')),
  budget_range text CHECK (budget_range IS NULL OR budget_range IN ('exploring', 'defined', 'investment-ready')),
  timeline text CHECK (timeline IS NULL OR timeline IN ('as-soon-as-possible', 'one-to-three-months', 'planning-ahead', 'flexible')),
  project_description text NOT NULL CHECK (char_length(project_description) BETWEEN 20 AND 2000),
  current_state text CHECK (current_state IS NULL OR char_length(current_state) <= 300),
  project_scope text CHECK (project_scope IS NULL OR char_length(project_scope) <= 500),
  preferred_contact_method text NOT NULL CHECK (preferred_contact_method IN ('email', 'whatsapp', 'phone')),
  status text NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'CONTACTED', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST')),
  source text NOT NULL CHECK (source IN ('quote', 'contact')),
  landing_page text NOT NULL CHECK (char_length(landing_page) <= 500),
  referrer text,
  utm_source text,
  utm_medium text,
  utm_campaign text,
  utm_content text,
  utm_term text,
  first_touch_data jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_touch_data jsonb NOT NULL DEFAULT '{}'::jsonb,
  consent_privacy boolean NOT NULL CHECK (consent_privacy),
  privacy_version text NOT NULL CHECK (char_length(privacy_version) <= 40),
  notification_status text NOT NULL DEFAULT 'PENDING' CHECK (notification_status IN ('PENDING', 'NOT_CONFIGURED', 'SENT', 'PARTIAL_FAILED', 'FAILED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.lead_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES public.leads(id) ON DELETE RESTRICT,
  event_type text NOT NULL CHECK (event_type IN ('LEAD_CREATED', 'EMAIL_NOTIFICATION_ATTEMPTED', 'EMAIL_NOTIFICATION_SENT', 'EMAIL_NOTIFICATION_FAILED', 'CLIENT_CONFIRMATION_ATTEMPTED', 'CLIENT_CONFIRMATION_SENT', 'CLIENT_CONFIRMATION_FAILED')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX leads_status_created_at_idx ON public.leads (status, created_at DESC);

CREATE INDEX leads_source_created_at_idx ON public.leads (source, created_at DESC);

CREATE INDEX lead_events_lead_id_created_at_idx ON public.lead_events (lead_id, created_at);

CREATE OR REPLACE FUNCTION public.set_lead_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER leads_set_updated_at
BEFORE UPDATE ON public.leads
FOR EACH ROW EXECUTE FUNCTION public.set_lead_updated_at();

CREATE OR REPLACE FUNCTION public.submit_lead(
  p_submission_key uuid,
  p_name text,
  p_email text,
  p_phone text,
  p_company text,
  p_service text,
  p_budget_range text,
  p_timeline text,
  p_project_description text,
  p_current_state text,
  p_project_scope text,
  p_preferred_contact_method text,
  p_source text,
  p_landing_page text,
  p_referrer text,
  p_utm_source text,
  p_utm_medium text,
  p_utm_campaign text,
  p_utm_content text,
  p_utm_term text,
  p_first_touch_data jsonb,
  p_last_touch_data jsonb,
  p_consent_privacy boolean,
  p_privacy_version text
)
RETURNS TABLE (lead_id uuid, public_id text, created boolean)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
  inserted_id uuid;
  inserted_public_id text;
BEGIN
  INSERT INTO public.leads (
    submission_key, name, email, phone, company, service, budget_range,
    timeline, project_description, current_state, project_scope,
    preferred_contact_method, source, landing_page, referrer, utm_source,
    utm_medium, utm_campaign, utm_content, utm_term, first_touch_data,
    last_touch_data, consent_privacy, privacy_version
  ) VALUES (
    p_submission_key, p_name, p_email, p_phone, p_company, p_service,
    p_budget_range, p_timeline, p_project_description, p_current_state,
    p_project_scope, p_preferred_contact_method, p_source, p_landing_page,
    p_referrer, p_utm_source, p_utm_medium, p_utm_campaign, p_utm_content,
    p_utm_term, p_first_touch_data, p_last_touch_data, p_consent_privacy,
    p_privacy_version
  ) ON CONFLICT (submission_key) DO NOTHING
  RETURNING id, leads.public_id INTO inserted_id, inserted_public_id;

  IF inserted_id IS NOT NULL THEN
    INSERT INTO public.lead_events (lead_id, event_type)
    VALUES (inserted_id, 'LEAD_CREATED');
    RETURN QUERY SELECT inserted_id, inserted_public_id, true;
    RETURN;
  END IF;

  RETURN QUERY
  SELECT l.id, l.public_id, false
  FROM public.leads AS l
  WHERE l.submission_key = p_submission_key;
END;
$$;

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.lead_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.leads FROM anon, authenticated;

REVOKE ALL ON TABLE public.lead_events FROM anon, authenticated;

REVOKE ALL ON FUNCTION public.submit_lead(
  uuid, text, text, text, text, text, text, text, text, text, text, text,
  text, text, text, text, text, text, text, text, jsonb, jsonb, boolean, text
) FROM PUBLIC, anon, authenticated;
