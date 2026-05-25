Feature: Métricas de asistencia

  Background:
    Given existen citas registradas en el sistema
    And el administrador inicia sesion en el sistema

  Scenario: Generar métricas de asistencia
    Given el administrador accede al módulo de métricas
    When solicita el reporte de asistencia
    Then el sistema calcula las estadísticas correspondientes

  Scenario: Consulta de cumplimiento
    Given el administrador accede al módulo de métricas
    When el administrador revisa el reporte
    Then el sistema muestra el porcentaje de asistencia de los usuarios
