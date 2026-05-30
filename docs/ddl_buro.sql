-- ================================================================
-- DDL — Buró Jurídico ICESI
-- Base de datos: PostgreSQL 15 (Supabase)
-- Generado: 2026-05-24
-- ================================================================

-- ----------------------------------------------------------------
-- MÓDULO: Autenticación y Roles (Django auth + accounts)
-- ----------------------------------------------------------------

CREATE TABLE auth_group (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_user (
    id           SERIAL PRIMARY KEY,
    username     VARCHAR(150) NOT NULL UNIQUE,
    password     VARCHAR(128) NOT NULL,
    email        VARCHAR(254) NOT NULL,
    first_name   VARCHAR(150) NOT NULL DEFAULT '',
    last_name    VARCHAR(150) NOT NULL DEFAULT '',
    is_superuser BOOLEAN      NOT NULL DEFAULT FALSE,
    is_staff     BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    date_joined  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login   TIMESTAMPTZ
);

CREATE TABLE auth_user_groups (
    id       BIGSERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE (user_id, group_id)
);

CREATE TABLE accounts_userprofile (
    id                       BIGSERIAL PRIMARY KEY,
    user_id                  INTEGER      NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    max_cases                INTEGER      NOT NULL DEFAULT 5,
    availability             BOOLEAN      NOT NULL DEFAULT TRUE,
    preferred_room           VARCHAR(20),
    student_code             VARCHAR(50),
    supervising_professor_id INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------
-- MÓDULO: Beneficiarios
-- ----------------------------------------------------------------

CREATE TABLE beneficiary_beneficiary (
    id                       VARCHAR(200) PRIMARY KEY,
    name                     VARCHAR(200) NOT NULL,
    location                 VARCHAR(300) NOT NULL,
    phone                    VARCHAR(512) NOT NULL,  -- cifrado Fernet
    email                    VARCHAR(254) NOT NULL,
    date_register            DATE         NOT NULL,
    colombian_identification VARCHAR(512) NOT NULL   -- cifrado Fernet
);

CREATE TABLE beneficiary_documentbeneficiary (
    id             BIGSERIAL    PRIMARY KEY,
    file           VARCHAR(100) NOT NULL,
    date_upload    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    beneficiary_id VARCHAR(200) NOT NULL REFERENCES beneficiary_beneficiary(id) ON DELETE CASCADE
);

CREATE TABLE beneficiary_datadeletionrequest (
    id             BIGSERIAL    PRIMARY KEY,
    request_date   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    status         VARCHAR(20)  NOT NULL DEFAULT 'pending',
    reason         TEXT         NOT NULL,
    beneficiary_id VARCHAR(200) NOT NULL REFERENCES beneficiary_beneficiary(id) ON DELETE CASCADE
);

CREATE TABLE beneficiary_beneficiaryauditlog (
    id                  BIGSERIAL    PRIMARY KEY,
    action              VARCHAR(20)  NOT NULL,
    description         TEXT         NOT NULL,
    changed_fields      JSONB,
    beneficiary_document VARCHAR(30) NOT NULL DEFAULT '',
    beneficiary_name    VARCHAR(200) NOT NULL DEFAULT '',
    timestamp           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ip_address          INET,
    beneficiary_id      VARCHAR(200) REFERENCES beneficiary_beneficiary(id) ON DELETE SET NULL,
    user_id             INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------
-- MÓDULO: Casos
-- ----------------------------------------------------------------

CREATE TABLE cases_case (
    id                    BIGSERIAL    PRIMARY KEY,
    code                  VARCHAR(20)  NOT NULL UNIQUE,
    status                VARCHAR(20)  NOT NULL DEFAULT 'open',
    sala                  VARCHAR(20),
    description           TEXT,
    state                 VARCHAR(100) NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deadline_date         DATE,
    deadline_alert_sent_at TIMESTAMPTZ,
    rejection_reason      TEXT,
    assigned_student_id   INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL,
    beneficiary_id        VARCHAR(200) REFERENCES beneficiary_beneficiary(id) ON DELETE SET NULL,
    created_by_id         INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE cases_casedocument (
    id          BIGSERIAL    PRIMARY KEY,
    file        VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    case_id     BIGINT       NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE
);

CREATE TABLE cases_communicationinteraction (
    id               BIGSERIAL    PRIMARY KEY,
    interaction_type VARCHAR(20)  NOT NULL,
    direction        VARCHAR(10)  NOT NULL,
    description      TEXT         NOT NULL,
    timestamp        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    audio_file       VARCHAR(200),               -- URL Cloudinary para grabaciones .webm
    case_id          BIGINT       NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE,
    registered_by_id INTEGER      REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE cases_callsession (
    id            BIGSERIAL   PRIMARY KEY,
    room_id       VARCHAR(64) NOT NULL UNIQUE,
    offer_sdp     TEXT,                          -- SDP del caller (WebRTC)
    answer_sdp    TEXT,                          -- SDP del callee (WebRTC)
    status        VARCHAR(20) NOT NULL DEFAULT 'waiting',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    case_id       BIGINT      NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE,
    created_by_id INTEGER     REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE cases_caseauditlog (
    id              BIGSERIAL   PRIMARY KEY,
    action          VARCHAR(20) NOT NULL,
    description     TEXT        NOT NULL,
    previous_status VARCHAR(50),
    new_status      VARCHAR(50),
    case_radicado   VARCHAR(50) NOT NULL DEFAULT '',
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address      INET,
    case_id         BIGINT      REFERENCES cases_case(id) ON DELETE SET NULL,
    user_id         INTEGER     REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE cases_casereassignmentlog (
    id             BIGSERIAL   PRIMARY KEY,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    case_id        BIGINT      NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE,
    changed_by_id  INTEGER     NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    old_student_id INTEGER     REFERENCES auth_user(id) ON DELETE SET NULL,
    new_student_id INTEGER     REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE cases_caseevaluation (
    id           BIGSERIAL   PRIMARY KEY,
    score        SMALLINT,
    feedback     TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    case_id      BIGINT      NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE,
    professor_id INTEGER     REFERENCES auth_user(id) ON DELETE SET NULL,
    student_id   INTEGER     NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

CREATE TABLE cases_notification (
    id               BIGSERIAL    PRIMARY KEY,
    notification_type VARCHAR(20) NOT NULL,
    title            VARCHAR(200) NOT NULL,
    message          TEXT         NOT NULL,
    previous_status  VARCHAR(50),
    new_status       VARCHAR(50),
    is_read          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    read_at          TIMESTAMPTZ,
    case_id          BIGINT       NOT NULL REFERENCES cases_case(id) ON DELETE CASCADE,
    recipient_user_id INTEGER     NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------
-- MÓDULO: Citas
-- ----------------------------------------------------------------

CREATE TABLE cite_cite (
    id            SERIAL       PRIMARY KEY,
    date_assigned DATE         NOT NULL,
    modality_cite VARCHAR(20)  NOT NULL,
    state_cite    VARCHAR(20)  NOT NULL DEFAULT 'scheduled',
    request_cite  VARCHAR(20)  NOT NULL,
    description   VARCHAR(2000) NOT NULL,
    reminder_sent BOOLEAN      NOT NULL DEFAULT FALSE,
    beneficiary_id VARCHAR(200) NOT NULL REFERENCES beneficiary_beneficiary(id) ON DELETE CASCADE
);
