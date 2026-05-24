Feature: Panel academico de profesores

  Background:
    Given existen estudiantes registrados en el sistema

  Scenario: Visualizacion del panel academico
    Given el profesor accede al sistema
    When abre el panel de control academico
    Then el sistema muestra metricas y progreso de los estudiantes

  Scenario: Consulta de desempeno
    Given el profesor selecciona un estudiante
    When consulta su informacion
    Then el sistema muestra su desempeno y casos asignados
