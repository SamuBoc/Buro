Feature: Historial academico

  Background:
    Given existe un estudiante registrado

  Scenario: Consulta del historial
    Given el profesor accede al perfil del estudiante
    When consulta su historial academico
    Then el sistema muestra los casos gestionados y evaluaciones

  Scenario: Visualizacion de retroalimentacion
    Given existen evaluaciones registradas
    When el profesor revisa el historial
    Then el sistema muestra la retroalimentacion correspondiente
