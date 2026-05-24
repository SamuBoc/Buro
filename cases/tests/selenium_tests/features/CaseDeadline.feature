Feature: Registro de fecha limite del caso
  Background:
    Given existe un caso registrado en el sistema con fecha limite

  Scenario: Registro exitoso de fecha limite
    Given la secretaria accede al detalle del caso para registrar fecha limite
    When ingresa una fecha limite de atencion
    Then el sistema guarda la fecha asociada al caso

  Scenario: Generacion de alerta
    Given existe un caso con fecha limite proxima
    When faltan pocos dias para el vencimiento
    Then el sistema genera una alerta para los responsables del caso
