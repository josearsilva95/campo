-- ============================================================
-- CONTROLE DE VIAGEM — Schema Supabase / PostgreSQL
-- Execute este arquivo no SQL Editor do Supabase
-- ============================================================

-- USUÁRIOS
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nome TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  senha_hash TEXT NOT NULL,
  telefone TEXT,
  perfil TEXT NOT NULL DEFAULT 'tecnico', -- 'adm' ou 'tecnico'
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- VIAGENS
CREATE TABLE IF NOT EXISTS viagens (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  obra TEXT NOT NULL,
  data_saida DATE NOT NULL,
  data_retorno_prevista DATE,
  data_retorno_real DATE,
  carro TEXT NOT NULL,
  placa TEXT NOT NULL,
  responsavel_id UUID REFERENCES usuarios(id),
  caixa_valor NUMERIC(10,2) NOT NULL DEFAULT 0,
  caixa_transferido NUMERIC(10,2) DEFAULT 0,
  observacoes TEXT,
  status TEXT DEFAULT 'ativa', -- 'ativa', 'encerramento_pendente', 'encerrada'
  saldo_devolvido NUMERIC(10,2),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- TÉCNICOS POR VIAGEM
CREATE TABLE IF NOT EXISTS tecnicos_viagem (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  viagem_id UUID REFERENCES viagens(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- GASTOS
CREATE TABLE IF NOT EXISTS gastos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  viagem_id UUID REFERENCES viagens(id) ON DELETE CASCADE,
  categoria TEXT NOT NULL, -- 'combustivel','pedagio','alimentacao','hospedagem','material','outros'
  descricao TEXT,
  valor NUMERIC(10,2) NOT NULL,
  foto_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- PARADAS / DESVIOS DE ROTA
CREATE TABLE IF NOT EXISTS paradas (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  viagem_id UUID REFERENCES viagens(id) ON DELETE CASCADE,
  local TEXT NOT NULL,
  tipo TEXT NOT NULL, -- 'material','documento','nova_obra','outro'
  instrucoes TEXT,
  notificado BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- CHECKLISTS
CREATE TABLE IF NOT EXISTS checklists (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  viagem_id UUID REFERENCES viagens(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL, -- 'saida' ou 'retorno'
  km INTEGER,
  pneus BOOLEAN DEFAULT false,
  combustivel BOOLEAN DEFAULT false,
  oleo BOOLEAN DEFAULT false,
  agua BOOLEAN DEFAULT false,
  lanternas BOOLEAN DEFAULT false,
  macaco BOOLEAN DEFAULT false,
  extintor BOOLEAN DEFAULT false,
  documentos BOOLEAN DEFAULT false,
  observacoes TEXT,
  fotos_urls TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

-- PONTO DE HORAS
CREATE TABLE IF NOT EXISTS pontos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  viagem_id UUID REFERENCES viagens(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id),
  data DATE NOT NULL,
  saida_hotel TIME,
  chegada_obra TIME,
  saida_obra TIME,
  chegada_hotel TIME,
  total_horas NUMERIC(4,2),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(viagem_id, usuario_id, data)
);

-- ============================================================
-- Supabase Storage: criar bucket "notas" via dashboard
-- Settings > Storage > New Bucket > nome: notas > Public: true
-- ============================================================
