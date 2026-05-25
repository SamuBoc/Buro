Feature: Registro de nuevo caso juridico (HU-6)

  Background:
    Given la secretaria ha iniciado sesion en el sistema
    And existe un beneficiario previamente registrado

  Scenario: Registro exitoso de un caso
    Given la secretaria accede al formulario de registro de caso
    When selecciona la sala juridica
    And ingresa la descripcion del problema
    And carga los documentos soporte
    And hace clic en "Registrar caso"
    Then el sistema guarda la informacion del caso
    And asocia el caso al beneficiario correspondiente

  Scenario: Campos obligatorios incompletos
    Given la secretaria accede al formulario de registro de caso
    And la secretaria intenta registrar un caso
    When no selecciona la sala juridica o no ingresa la descripcion
    Then el sistema muestra un mensaje indicando que los campos obligatorios deben completarse
    And no permite registrar el caso
