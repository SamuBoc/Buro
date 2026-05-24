Feature: Reasignacion manual de casos
  Background:
    Given existe un caso asignado a un estudiante

  Scenario: Reasignacion exitosa
    Given la secretaria accede al detalle del caso
    When selecciona un nuevo estudiante
    And confirma la reasignacion
    Then el sistema actualiza el estudiante responsable del caso
    And registra la accion en la bitacora

  Scenario: Usuario sin permisos
    Given un usuario sin permisos intenta reasignar un caso
    When intenta realizar la reasignacion
    Then el sistema bloquea la accion
    And muestra un mensaje indicando que no tiene permisos
