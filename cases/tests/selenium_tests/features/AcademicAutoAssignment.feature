Feature: Asignacion automatica academica (HU-26)

  Background:
    Given existen estudiantes registrados en el sistema

  Scenario: Asignacion automatica
    Given se registra un nuevo caso
    When el sistema evalua los criterios de asignacion
    Then asigna el caso al estudiante mas adecuado

  Scenario: Estudiante sin disponibilidad
    Given un estudiante tiene su carga completa
    When el sistema evalua la asignacion
    Then el sistema selecciona otro estudiante disponible
