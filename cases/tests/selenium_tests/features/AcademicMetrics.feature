Feature: Metricas academicas (HU-27)

  Background:
    Given existen datos academicos registrados

  Scenario: Generar reporte academico
    Given el profesor accede al modulo de metricas
    When aplica filtros por estudiante o tipo de caso
    Then el sistema muestra las estadisticas correspondientes

  Scenario: Consulta de desempeno
    Given existen metricas registradas
    When el profesor revisa el desempeno del estudiante
    Then el sistema muestra indicadores academicos asociados
