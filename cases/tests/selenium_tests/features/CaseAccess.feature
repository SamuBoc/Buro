Feature: Control de acceso a casos (HU-12)

  Background:
    Given existe un caso registrado en el sistema

  Scenario: Acceso autorizado
    Given el estudiante asignado intenta acceder al caso
    When abre el detalle del caso
    Then el sistema muestra toda la informacion del expediente

  Scenario: Acceso no autorizado
    Given un usuario no autorizado intenta acceder al caso
    When intenta abrir el detalle completo
    Then el sistema bloquea el acceso
    And muestra un mensaje indicando que no tiene permisos
