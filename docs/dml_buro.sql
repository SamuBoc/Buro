-- ================================================================
-- DML — Buró Jurídico ICESI
-- Datos iniciales (seed) para el sistema
-- Base de datos: PostgreSQL 15 (Supabase)
-- Generado: 2026-05-24
-- Ejecución: python manage.py seed_roles  (crea los grupos)
--            Luego insertar los usuarios desde el admin de Django
-- ================================================================

-- ----------------------------------------------------------------
-- Roles del sistema (grupos de Django)
-- Generados por: python manage.py seed_roles
-- ----------------------------------------------------------------

INSERT INTO auth_group (id, name) VALUES (1, 'administrador');
INSERT INTO auth_group (id, name) VALUES (2, 'secretaria');
INSERT INTO auth_group (id, name) VALUES (3, 'estudiante');
INSERT INTO auth_group (id, name) VALUES (4, 'profesor');

-- ----------------------------------------------------------------
-- Usuarios de prueba / demostración
-- Contraseña de todos: Buro2026!
-- ----------------------------------------------------------------

INSERT INTO auth_user (id, username, email, is_superuser, is_staff, is_active, first_name, last_name, date_joined, password)
VALUES
  (1, 'admin',      'admin@buro.icesi.edu.co',      TRUE,  TRUE,  TRUE, 'Admin',      'Buro',      NOW(), '<hash>'),
  (2, 'secretaria', 'secretaria@buro.icesi.edu.co', FALSE, FALSE, TRUE, 'Secretaria', 'Buro',      NOW(), '<hash>'),
  (3, 'estudiante', 'estudiante@buro.icesi.edu.co', FALSE, FALSE, TRUE, 'Estudiante', 'Buro',      NOW(), '<hash>'),
  (4, 'profesor',   'profesor@buro.icesi.edu.co',   FALSE, FALSE, TRUE, 'Profesor',   'Buro',      NOW(), '<hash>');

-- Asignación de roles a usuarios
INSERT INTO auth_user_groups (user_id, group_id) VALUES (1, 1); -- admin      → administrador
INSERT INTO auth_user_groups (user_id, group_id) VALUES (2, 2); -- secretaria → secretaria
INSERT INTO auth_user_groups (user_id, group_id) VALUES (3, 3); -- estudiante → estudiante
INSERT INTO auth_user_groups (user_id, group_id) VALUES (4, 4); -- profesor   → profesor

-- ----------------------------------------------------------------
-- Perfiles de usuario
-- ----------------------------------------------------------------

INSERT INTO accounts_userprofile (user_id, max_cases, availability)
VALUES
  (1, 99, TRUE),  -- admin
  (2, 99, TRUE),  -- secretaria
  (3, 5,  TRUE),  -- estudiante (máx 5 casos asignados)
  (4, 99, TRUE);  -- profesor

-- ----------------------------------------------------------------
-- Nota sobre los 36 casos y beneficiarios en producción
-- ----------------------------------------------------------------
-- Los 36 casos y sus beneficiarios asociados fueron cargados
-- manualmente desde la interfaz de administración de la plataforma
-- (rol secretaria/administrador) para efectos de demostración.
-- No existe un script automatizado para estos datos ya que
-- corresponden a datos simulados del consultorio jurídico.
--
-- Para regenerar datos de prueba se puede usar el admin de Django:
--   https://buro-2wvs.onrender.com/admin/
