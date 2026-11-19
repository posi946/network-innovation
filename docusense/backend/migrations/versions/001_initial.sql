-- DocuSense Africa v2 initial schema (Day 2)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  owner_id UUID,
  plan TEXT CHECK (plan IN ('business','elite')) DEFAULT 'business',
  seat_count INT DEFAULT 5 CHECK (seat_count BETWEEN 1 AND 100),
  invite_token TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT DEFAULT '',
  email TEXT,
  companion_name TEXT DEFAULT 'Lex' CHECK (char_length(companion_name) BETWEEN 1 AND 20),
  companion_color TEXT DEFAULT 'violet' CHECK (companion_color IN ('violet','cyan','gold','ember','arctic','jade','rose','solar')),
  companion_voice TEXT DEFAULT 'nova' CHECK (companion_voice IN ('nova','sterling','quinn','sydney','anika','amara','zara','lena','sage')),
  preferred_language TEXT DEFAULT 'en' CHECK (preferred_language IN ('en','fr','ar','pt','sw','yo','ha','ig','es','de','zh','hi')),
  plan TEXT CHECK (plan IN ('free','pro','business','elite')) DEFAULT 'free',
  default_jurisdiction TEXT DEFAULT 'NG',
  analyses_this_month INT DEFAULT 0,
  generates_this_month INT DEFAULT 0,
  usage_reset_at TIMESTAMPTZ,
  paystack_customer_id TEXT,
  is_active BOOL DEFAULT TRUE,
  onboarding_complete BOOL DEFAULT FALSE,
  analytics_opted_out BOOL DEFAULT FALSE,
  tos_accepted_at TIMESTAMPTZ,
  tos_version TEXT,
  organization_id UUID REFERENCES organizations(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organization_members (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('owner','admin','member')) DEFAULT 'member',
  invited_at TIMESTAMPTZ, joined_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL, original_name TEXT, file_type TEXT, file_size_kb INT,
  storage_path TEXT, storage_bucket TEXT DEFAULT 'documents',
  jurisdiction TEXT DEFAULT 'NG', raw_text TEXT, was_camera BOOL DEFAULT FALSE,
  ocr_used BOOL DEFAULT FALSE, deleted_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES documents(id), user_id UUID REFERENCES user_profiles(id),
  jurisdiction TEXT, document_type TEXT,
  risk_level TEXT CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  risk_score SMALLINT CHECK (risk_score BETWEEN 0 AND 100),
  overall_verdict TEXT CHECK (overall_verdict IN ('SIGN','NEGOTIATE','DO NOT SIGN')),
  verdict_reason TEXT, summary TEXT, jurisdiction_notes TEXT,
  red_flags JSONB DEFAULT '[]', missing_clauses JSONB DEFAULT '[]',
  negotiation_points JSONB DEFAULT '[]', questions_to_ask JSONB DEFAULT '[]',
  law_context_used JSONB DEFAULT '[]', model_used TEXT DEFAULT 'claude-sonnet-4-20250514',
  duration_ms INT, was_image_analysis BOOL DEFAULT FALSE,
  user_plan_at_time TEXT, feedback SMALLINT CHECK (feedback IN (-1,1)),
  created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  doc_type TEXT, title TEXT, jurisdiction TEXT, party_a TEXT, party_b TEXT,
  requirements TEXT, content TEXT, storage_path TEXT, model_used TEXT,
  duration_ms INT, download_count INT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  session_id UUID DEFAULT uuid_generate_v4(), analysis_id UUID REFERENCES analyses(id),
  chat_type TEXT CHECK (chat_type IN ('document','advisor','student','irac','voice')),
  jurisdiction TEXT, role TEXT CHECK (role IN ('user','assistant')),
  content TEXT, message_index INT DEFAULT 0, mode TEXT, citations JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS law_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  country TEXT NOT NULL,
  law_type TEXT CHECK (law_type IN ('constitution','statute','regulation','case_law','treaty')),
  law_title TEXT, section TEXT, subsection TEXT, content TEXT,
  language TEXT DEFAULT 'en', source_url TEXT,
  embedding vector(1024), seeded_at TIMESTAMPTZ, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS voice_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  session_id UUID DEFAULT uuid_generate_v4(), jurisdiction TEXT, companion_name TEXT,
  wake_word_count INT DEFAULT 0, total_turns INT DEFAULT 0, duration_seconds INT,
  intents_used JSONB DEFAULT '[]', created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID, action TEXT, ip_address TEXT, user_agent TEXT, endpoint TEXT,
  method TEXT, status_code INT, duration_ms INT, resource_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feature_flags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  flag_key TEXT UNIQUE NOT NULL, description TEXT, enabled BOOL DEFAULT FALSE,
  rollout_percent INT DEFAULT 0 CHECK (rollout_percent BETWEEN 0 AND 100),
  allowed_plans TEXT[] DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS law_chunks_embedding_hnsw ON law_chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX IF NOT EXISTS idx_documents_user_created ON documents(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, message_index);
CREATE INDEX IF NOT EXISTS idx_feature_flags_plans ON feature_flags USING GIN (allowed_plans);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE law_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;

CREATE POLICY own_rows ON documents USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY own_rows ON analyses USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY own_rows ON generated_documents USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY own_rows ON chat_messages USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY own_rows ON voice_sessions USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY read_laws ON law_chunks FOR SELECT TO authenticated USING (true);
CREATE POLICY insert_audit ON audit_logs FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY read_flags ON feature_flags FOR SELECT TO authenticated USING (true);

CREATE OR REPLACE FUNCTION check_plan_limit(p_user UUID, p_action TEXT) RETURNS BOOL AS $$
  SELECT CASE WHEN p_action = 'analyses'
    THEN analyses_this_month < CASE plan WHEN 'free' THEN 2 ELSE 100000 END
    ELSE generates_this_month < CASE plan WHEN 'free' THEN 1 ELSE 100000 END
  END FROM user_profiles WHERE id = p_user;
$$ LANGUAGE SQL SECURITY DEFINER;

CREATE OR REPLACE FUNCTION is_feature_enabled(p_flag TEXT, p_plan TEXT) RETURNS BOOL AS $$
  SELECT COALESCE(bool_or(enabled AND rollout_percent >= 50 AND p_plan = ANY(allowed_plans)), false)
  FROM feature_flags WHERE flag_key = p_flag;
$$ LANGUAGE SQL SECURITY DEFINER;

CREATE OR REPLACE FUNCTION log_tos_acceptance(p_user UUID, p_version TEXT) RETURNS VOID AS $$
  UPDATE user_profiles SET tos_accepted_at = NOW(), tos_version = p_version WHERE id = p_user;
$$ LANGUAGE SQL SECURITY DEFINER;

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_touch_user BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_touch_analyses BEFORE UPDATE ON analyses FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
