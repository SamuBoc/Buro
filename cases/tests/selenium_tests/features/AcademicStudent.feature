Feature: Registro de estudiantes (HU-25)

  Background:
    Given el administrador accede al modulo academico

  Scenario: Registro de estudiante
    Given el administrador ingresa los datos del estudiante
    When registra la carga academica correspondiente
    Then el sistema guarda la informacion del estudiante

  Scenario: Consulta de carga academica
    Given existen estudiantes registrados
    When el administrador consulta su informacion
    Then el sistema muestra los casos asignados y su carga actual
